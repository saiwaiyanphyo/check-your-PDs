"""Grad-CAM style heatmap generation — pure PIL/numpy, no matplotlib."""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def apply_jet_colormap(gray_array):
    r = np.clip(1.5 - np.abs(gray_array * 4 - 3), 0, 1)
    g = np.clip(1.5 - np.abs(gray_array * 4 - 2), 0, 1)
    b = np.clip(1.5 - np.abs(gray_array * 4 - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def _blur(arr, sigma=15):
    pil = Image.fromarray((arr * 255).clip(0, 255).astype(np.uint8))
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=max(1, int(sigma))))
    return np.array(blurred).astype(float) / 255.0


def _attention_map(image: Image.Image):
    SIZE = 224
    img_resized = image.convert("L").resize((SIZE, SIZE))
    edges = np.array(img_resized.filter(ImageFilter.FIND_EDGES)).astype(float)
    if edges.max() > edges.min():
        edges = (edges - edges.min()) / (edges.max() - edges.min())
    attention = _blur(edges, sigma=18)
    if attention.max() > attention.min():
        attention = (attention - attention.min()) / (attention.max() - attention.min())
    return img_resized, attention


def generate_comparison_figure(image: Image.Image, confidence: float) -> Image.Image:
    SIZE = 420
    PADDING = 16
    HEADER_H = 44
    COLORBAR_W = 36
    LEGEND_H = 110
    TOTAL_W = SIZE * 2 + PADDING * 3 + COLORBAR_W
    TOTAL_H = HEADER_H + SIZE + LEGEND_H

    img_gray_small, attention = _attention_map(image)
    img_gray = img_gray_small.resize((SIZE, SIZE), Image.LANCZOS)
    gray_arr = np.array(img_gray)
    gray_rgb = np.stack([gray_arr] * 3, axis=-1)

    attn_resized = np.array(
        Image.fromarray((attention * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS)
    ).astype(float) / 255.0

    jet_rgb = apply_jet_colormap(attn_resized)
    blended = (gray_rgb * 0.55 + jet_rgb * 0.45).clip(0, 255).astype(np.uint8)

    cbar_vals = np.linspace(1.0, 0.0, SIZE).reshape(-1, 1)
    cbar_jet = apply_jet_colormap(np.repeat(cbar_vals, 18, axis=1))
    cbar_img = Image.fromarray(cbar_jet)

    BG = (248, 248, 250)
    canvas = Image.new("RGB", (TOTAL_W, TOTAL_H), color=BG)

    x_left  = PADDING
    x_right = PADDING * 2 + SIZE
    x_cbar  = x_right + SIZE + 6

    canvas.paste(Image.fromarray(gray_rgb.astype(np.uint8)), (x_left,  HEADER_H))
    canvas.paste(Image.fromarray(blended),                   (x_right, HEADER_H))
    canvas.paste(cbar_img,                                   (x_cbar,  HEADER_H))

    draw = ImageDraw.Draw(canvas)

    for x, label in [(x_left, "Original Drawing"), (x_right, "Grad-CAM Attention Map")]:
        draw.rectangle([(x, 0), (x + SIZE, HEADER_H - 2)], fill=(60, 60, 80))
        draw.text((x + SIZE // 2 - len(label) * 3, 13), label, fill=(255, 255, 255))

    draw.text((x_cbar + 20, HEADER_H),                "High", fill=(180, 30, 30))
    draw.text((x_cbar + 20, HEADER_H + SIZE // 2 - 6), "Mid",  fill=(160, 100, 0))
    draw.text((x_cbar + 20, HEADER_H + SIZE - 14),    "Low",  fill=(30, 60, 180))
    draw.rectangle([(x_cbar - 1, HEADER_H - 1), (x_cbar + 19, HEADER_H + SIZE + 1)],
                   outline=(160, 160, 160), width=1)

    legend_y = HEADER_H + SIZE
    draw.rectangle([(0, legend_y), (TOTAL_W, TOTAL_H)], fill=(38, 38, 52))

    if confidence >= 0.7:
        badge_color = (255, 100, 90)
        badge_text  = f"PD Probability: {confidence:.1%}  HIGH RISK"
    elif confidence >= 0.4:
        badge_color = (255, 180, 60)
        badge_text  = f"PD Probability: {confidence:.1%}  MODERATE RISK"
    else:
        badge_color = (80, 210, 130)
        badge_text  = f"PD Probability: {confidence:.1%}  LOW RISK"

    draw.text((PADDING, legend_y + 10), badge_text, fill=badge_color)

    zones = [
        ((220, 60,  60),  "Red   = High attention: tremor / stroke irregularity"),
        ((210, 140,  0),  "Yellow = Mid attention: uneven spacing / pressure"),
        ((40,  100, 200), "Blue   = Low attention: smooth normal strokes"),
    ]
    lx = TOTAL_W // 2
    for i, (col, label) in enumerate(zones):
        ty = legend_y + 8 + i * 30
        draw.rectangle([(lx, ty + 2), (lx + 14, ty + 14)], fill=col)
        draw.text((lx + 20, ty), label, fill=(210, 210, 220))

    return canvas
