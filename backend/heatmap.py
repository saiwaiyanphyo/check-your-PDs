"""Grad-CAM heatmap + anomaly region annotation — pure PIL/numpy, no matplotlib."""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ── Colormap ─────────────────────────────────────────────────────────────────

def _jet(arr: np.ndarray) -> np.ndarray:
    r = np.clip(1.5 - np.abs(arr * 4 - 3), 0, 1)
    g = np.clip(1.5 - np.abs(arr * 4 - 2), 0, 1)
    b = np.clip(1.5 - np.abs(arr * 4 - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def _blur(arr: np.ndarray, sigma: int = 15) -> np.ndarray:
    pil = Image.fromarray((arr * 255).clip(0, 255).astype(np.uint8))
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=max(1, int(sigma))))
    return np.array(blurred).astype(float) / 255.0


def _normalize(arr: np.ndarray) -> np.ndarray:
    mn, mx = arr.min(), arr.max()
    return (arr - mn) / (mx - mn) if mx > mn else arr


# ── Attention maps ────────────────────────────────────────────────────────────

def compute_gradcam(image: Image.Image, model) -> "np.ndarray | None":
    """
    Real Grad-CAM via TF GradientTape.
    Returns H×W float array normalised to [0, 1], or None on failure.
    """
    try:
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

        # Find the last layer that outputs a 4-D spatial feature map
        last_conv = None
        for layer in reversed(model.layers):
            if len(layer.output_shape) == 4:
                last_conv = layer
                break

        if last_conv is None:
            print("Grad-CAM: no 4-D layer found, falling back.")
            return None

        print(f"Grad-CAM: using layer '{last_conv.name}' {last_conv.output_shape}")

        grad_model = tf.keras.Model(
            inputs=model.inputs,
            outputs=[last_conv.output, model.output],
        )

        img = image.convert("RGB").resize((224, 224))
        arr = preprocess_input(np.array(img, dtype=np.float32))
        arr = np.expand_dims(arr, axis=0)

        with tf.GradientTape() as tape:
            conv_out, preds = grad_model(arr)
            pred = preds[0]
            # Support sigmoid (1 output) and softmax (2+ outputs)
            if pred.shape[-1] == 1 or len(pred.shape) == 0:
                score = pred[0] if pred.shape[-1] == 1 else pred
            else:
                score = pred[1] if pred.shape[-1] >= 2 else pred[0]

        grads = tape.gradient(score, conv_out)           # (1, h, w, c)
        pooled = tf.reduce_mean(grads, axis=(0, 1, 2))  # (c,)

        heatmap = (conv_out[0].numpy() * pooled.numpy()).mean(axis=-1)  # (h, w)
        heatmap = np.maximum(heatmap, 0)
        return _normalize(heatmap)

    except Exception as exc:
        print(f"Grad-CAM failed: {exc}")
        return None


def _stroke_irregularity(image: Image.Image) -> np.ndarray:
    """
    Stroke irregularity map via ink-segment fragmentation counting.

    How it works
    ------------
    The image is divided into 14×14-pixel patches (16×16 grid on 224 px).
    For each patch the number of ink "entries" per scan line is counted:

        smooth stroke  → exactly 1 ink segment per row/col  → score ≈ 0
        shaky stroke   → pen oscillates back across scan lines → 2+ segments
                         per row/col → score > 0

    score = max(0, avg_entries_per_inky_line − 1.0)

    Why this beats edge detection and gradient-orientation variance
    --------------------------------------------------------------
    • Edge detection fires wherever there is *any* stroke — smooth or shaky.
    • Gradient-orientation circular variance is confounded by the antiparallel
      gradients on the two sides of any stroke (both edges score "high variance").
    • Fragmentation is 0 for a single continuous stroke regardless of curvature,
      and rises only when the pen actually changes direction multiple times within
      the patch, which is the direct physical signature of tremor.
    """
    SIZE  = 224
    PATCH = 14          # → 16×16 grid (224 / 14 = 16)
    MIN_INK = 4         # minimum ink pixels needed for a patch to score

    img = image.convert("L").resize((SIZE, SIZE))
    arr = np.array(img, dtype=np.int16)

    # Adaptive threshold: dark ink on white background (most drawings)
    thresh = 180 if int(arr.mean()) > 128 else 80
    ink = (arr < thresh).astype(np.int8)  # 1 = ink, 0 = background

    gh = gw = SIZE // PATCH   # 16
    grid = np.zeros((gh, gw), dtype=float)

    for i in range(gh):
        for j in range(gw):
            y0, y1 = i * PATCH, (i + 1) * PATCH
            x0, x1 = j * PATCH, (j + 1) * PATCH
            p = ink[y0:y1, x0:x1]

            if int(p.sum()) < MIN_INK:
                continue

            # Horizontal: count 0→1 transitions per row (background → ink entries)
            h_entries   = (np.diff(p, axis=1) == 1).sum(axis=1)   # shape (PATCH,)
            h_inky_rows = (p.sum(axis=1) > 0).sum()

            # Vertical: count 0→1 transitions per column
            v_entries   = (np.diff(p, axis=0) == 1).sum(axis=0)   # shape (PATCH,)
            v_inky_cols = (p.sum(axis=0) > 0).sum()

            avg_h = h_entries.sum() / max(h_inky_rows, 1)
            avg_v = v_entries.sum() / max(v_inky_cols, 1)

            # Expected value for a single smooth stroke = 1.0.
            # Excess above 1 = extra stroke segments = fragmentation / tremor.
            score = max(0.0, max(avg_h, avg_v) - 1.0)
            grid[i, j] = score

    # Upsample 16×16 → 224×224 and smooth
    safe_max = grid.max() if grid.max() > 0 else 1.0
    grid_pil = Image.fromarray((grid / safe_max * 255).astype(np.uint8))
    up = np.array(grid_pil.resize((SIZE, SIZE), Image.BILINEAR)).astype(float) / 255.0
    return _normalize(_blur(up, sigma=9))


# ── Anomaly region detection ──────────────────────────────────────────────────

_POS_LABELS = {
    (0, 0): "Top-left",    (0, 1): "Top-center",    (0, 2): "Top-right",
    (1, 0): "Mid-left",    (1, 1): "Center",         (1, 2): "Mid-right",
    (2, 0): "Bottom-left", (2, 1): "Bottom-center",  (2, 2): "Bottom-right",
}

_SEVERITY = [
    (0.75, "severe tremor signature"),
    (0.50, "moderate stroke irregularity"),
    (0.30, "mild pressure variation"),
]


def find_anomaly_regions(attention: np.ndarray, max_regions: int = 3) -> list:
    """
    Non-max suppression over the 224×224 attention map.
    Returns up to `max_regions` dicts sorted by intensity (highest first):
      {id, x_norm, y_norm, intensity, label, severity}
    """
    H, W = attention.shape
    radius = max(H, W) // 5   # ~44 px suppression window

    att = attention.copy()
    regions = []

    for i in range(max_regions):
        iy, ix = np.unravel_index(np.argmax(att), att.shape)
        intensity = float(att[iy, ix])

        if intensity < 0.30:
            break

        x_norm = float(ix) / W
        y_norm = float(iy) / H
        row = min(int(y_norm * 3), 2)
        col = min(int(x_norm * 3), 2)
        pos = _POS_LABELS[(row, col)]

        severity = "minor variation"
        for threshold, desc in _SEVERITY:
            if intensity >= threshold:
                severity = desc
                break

        regions.append({
            "id": i + 1,
            "x_norm": round(x_norm, 3),
            "y_norm": round(y_norm, 3),
            "intensity": round(intensity, 3),
            "label": f"{pos} — {severity}",
            "severity": severity,
        })

        # Zero out a square neighbourhood so the next peak is elsewhere
        y1, y2 = max(0, iy - radius), min(H, iy + radius)
        x1, x2 = max(0, ix - radius), min(W, ix + radius)
        att[y1:y2, x1:x2] = 0

    return regions


# ── Marker overlay ────────────────────────────────────────────────────────────

def _marker_color(intensity: float) -> tuple:
    if intensity >= 0.75:
        return (255, 55, 55)
    if intensity >= 0.50:
        return (255, 170, 0)
    return (70, 140, 255)


def _draw_markers(
    draw: ImageDraw.ImageDraw,
    regions: list,
    panel_x: int,
    panel_y: int,
    panel_size: int,
):
    """Draw a numbered ring at each anomaly location on the heatmap panel."""
    r = 16
    for region in regions:
        px = panel_x + int(region["x_norm"] * panel_size)
        py = panel_y + int(region["y_norm"] * panel_size)
        color = _marker_color(region["intensity"])

        # White outer ring (visibility against dark/bright backgrounds)
        draw.ellipse(
            [(px - r - 3, py - r - 3), (px + r + 3, py + r + 3)],
            outline=(255, 255, 255),
            width=3,
        )
        # Coloured inner ring
        draw.ellipse(
            [(px - r, py - r), (px + r, py + r)],
            outline=color,
            width=2,
        )
        # Number centred in the ring (approximate for PIL's default bitmap font)
        label = str(region["id"])
        draw.text((px - 4, py - 7), label, fill=(255, 255, 255))


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_heatmap(
    image: Image.Image,
    model,
    confidence: float,
) -> tuple:
    """
    Build a side-by-side comparison figure with anomaly markers.

    Returns
    -------
    (PIL.Image, list[dict])
        The annotated figure and the list of anomaly region dicts.
    """
    SIZE = 420
    PAD = 16
    HEADER_H = 44
    CBAR_W = 36
    LEGEND_H = 145

    TOTAL_W = SIZE * 2 + PAD * 3 + CBAR_W
    TOTAL_H = HEADER_H + SIZE + LEGEND_H

    # ── Compute attention ──
    raw_attn = compute_gradcam(image, model) if model is not None else None
    using_gradcam = raw_attn is not None
    if raw_attn is None:
        raw_attn = _stroke_irregularity(image)

    # Resize to 224 for region detection, SIZE for drawing
    attn_pil = Image.fromarray((_normalize(raw_attn) * 255).astype(np.uint8))
    attn_224 = np.array(attn_pil.resize((224, 224), Image.LANCZOS)).astype(float) / 255.0
    attn_big = np.array(attn_pil.resize((SIZE, SIZE), Image.LANCZOS)).astype(float) / 255.0

    # ── Detect anomaly regions on 224×224 map ──
    anomaly_regions = find_anomaly_regions(attn_224, max_regions=3)

    # ── Build image panels ──
    img_display = image.convert("L").resize((SIZE, SIZE), Image.LANCZOS)
    gray = np.array(img_display)
    gray_rgb = np.stack([gray] * 3, axis=-1)

    jet_rgb = _jet(attn_big)
    blended = (gray_rgb * 0.50 + jet_rgb * 0.50).clip(0, 255).astype(np.uint8)

    cbar_vals = np.linspace(1.0, 0.0, SIZE).reshape(-1, 1)
    cbar_img = Image.fromarray(_jet(np.repeat(cbar_vals, 18, axis=1)))

    # ── Canvas ──
    canvas = Image.new("RGB", (TOTAL_W, TOTAL_H), color=(248, 248, 250))

    x_left  = PAD
    x_right = PAD * 2 + SIZE
    x_cbar  = x_right + SIZE + 6

    canvas.paste(Image.fromarray(gray_rgb.astype(np.uint8)), (x_left,  HEADER_H))
    canvas.paste(Image.fromarray(blended),                   (x_right, HEADER_H))
    canvas.paste(cbar_img,                                   (x_cbar,  HEADER_H))

    draw = ImageDraw.Draw(canvas)

    # Panel headers
    heatmap_label = "Grad-CAM (Real)" if using_gradcam else "Stroke Irregularity Map"
    for px, lbl in [(x_left, "Original Drawing"), (x_right, heatmap_label)]:
        draw.rectangle([(px, 0), (px + SIZE, HEADER_H - 2)], fill=(50, 50, 72))
        draw.text((px + SIZE // 2 - len(lbl) * 3, 13), lbl, fill=(255, 255, 255))

    # Colorbar
    draw.text((x_cbar + 20, HEADER_H),                  "High", fill=(180, 30,  30))
    draw.text((x_cbar + 20, HEADER_H + SIZE // 2 - 6),  "Mid",  fill=(160, 100,  0))
    draw.text((x_cbar + 20, HEADER_H + SIZE - 14),      "Low",  fill=(30,   60, 180))
    draw.rectangle(
        [(x_cbar - 1, HEADER_H - 1), (x_cbar + 19, HEADER_H + SIZE + 1)],
        outline=(160, 160, 160), width=1,
    )

    # Numbered anomaly markers on the heatmap panel
    _draw_markers(draw, anomaly_regions, x_right, HEADER_H, SIZE)

    # ── Legend bar ──
    legend_y = HEADER_H + SIZE
    draw.rectangle([(0, legend_y), (TOTAL_W, TOTAL_H)], fill=(35, 35, 50))

    # Confidence badge (left)
    if confidence >= 0.7:
        badge_col  = (255, 100, 90)
        badge_text = f"PD Probability: {confidence:.1%}  [HIGH RISK]"
    elif confidence >= 0.4:
        badge_col  = (255, 180, 60)
        badge_text = f"PD Probability: {confidence:.1%}  [MODERATE RISK]"
    else:
        badge_col  = (80, 210, 130)
        badge_text = f"PD Probability: {confidence:.1%}  [LOW RISK]"

    draw.text((PAD, legend_y + 8), badge_text, fill=badge_col)

    # Anomaly region list (left column below badge)
    if anomaly_regions:
        draw.text((PAD, legend_y + 28), "Detected regions:", fill=(155, 155, 175))
        for region in anomaly_regions:
            ty = legend_y + 46 + (region["id"] - 1) * 22
            col = _marker_color(region["intensity"])
            draw.text((PAD, ty), f"  [{region['id']}] {region['label']}", fill=col)

    # Colour legend (right column)
    lx = TOTAL_W // 2
    zones = [
        ((220,  60,  60), "Red    = High irregularity (tremor / shaky strokes)"),
        ((210, 140,   0), "Yellow = Moderate irregularity (uneven direction)"),
        ((40,  100, 200), "Blue   = Consistent smooth strokes"),
    ]
    for i, (col, lbl) in enumerate(zones):
        ty = legend_y + 12 + i * 34
        draw.rectangle([(lx, ty + 2), (lx + 14, ty + 14)], fill=col)
        draw.text((lx + 20, ty), lbl, fill=(210, 210, 220))

    return canvas, anomaly_regions
