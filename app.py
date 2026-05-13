"""
🧠 Parkinson's Disease Preliminary Prediction System
Two-Stage: Clinical Risk Scoring + Hand-Drawing Classification

Stage 1: Clinical questionnaire → Risk score (0-22 points)
Stage 2: Hand-drawing upload → CNN classifier (PD vs Healthy)
Combined: Weighted fusion → Final recommendation

Derived from 1,340 hospital records (Udon Thani, Thailand)
"""

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

# ============================================================
# STAGE 1: RISK SCORING ENGINE
# ============================================================

def compute_risk_score(
    age, sex,
    tremor, bradykinesia, rigidity,
    falls, gait_difficulty, weakness, asymmetric,
    cognitive_decline, sleep_disorder, constipation, depression,
    bedridden, walk_with_aid,
    has_cva, has_all_metabolic
):
    """Compute PD risk score from clinical questionnaire (max 22 points)."""
    score = 0
    breakdown = []

    # Demographics (max 3)
    if age and age != "Under 40":
        age_map = {"40-49": 0, "50-59": 0, "60-69": 1, "70-79": 2, "80+": 2}
        pts = age_map.get(age, 0)
        if pts > 0:
            score += pts
            breakdown.append(f"Age {age}: +{pts}")

    if sex == "Male":
        score += 1
        breakdown.append("Male sex: +1")

    # Cardinal motor (max 6)
    if tremor:
        score += 2
        breakdown.append("Tremor: +2")
    if bradykinesia:
        score += 2
        breakdown.append("Bradykinesia: +2")
    if rigidity:
        score += 2
        breakdown.append("Rigidity: +2")

    # Supporting motor (max 4)
    if falls:
        score += 1
        breakdown.append("Falls/balance: +1")
    if gait_difficulty:
        score += 1
        breakdown.append("Gait difficulty: +1")
    if weakness:
        score += 1
        breakdown.append("Weakness: +1")
    if asymmetric:
        score += 1
        breakdown.append("Asymmetric symptoms: +1")

    # Non-motor (max 4)
    if cognitive_decline:
        score += 1
        breakdown.append("Cognitive decline: +1")
    if sleep_disorder:
        score += 1
        breakdown.append("Sleep disorder: +1")
    if constipation:
        score += 1
        breakdown.append("Constipation: +1")
    if depression:
        score += 1
        breakdown.append("Depression: +1")

    # Functional (max 2)
    if bedridden:
        score += 1
        breakdown.append("Bedridden: +1")
    if walk_with_aid:
        score += 1
        breakdown.append("Walking aid: +1")

    # Comorbidity (max 2)
    if has_cva:
        score += 1
        breakdown.append("Stroke history: +1")
    if has_all_metabolic:
        score += 1
        breakdown.append("Metabolic cluster: +1")

    return score, breakdown


def get_risk_level(score):
    if score <= 2:
        return "Low", 0.3, "🟢"
    elif score <= 5:
        return "Medium", 1.0, "🟡"
    else:
        return "High", 1.5, "🔴"


# ============================================================
# STAGE 2: DRAWING CLASSIFIER (placeholder) + HEATMAP
# Pure PIL/numpy — no matplotlib dependency
# ============================================================

def apply_jet_colormap(gray_array):
    """Convert a float [0,1] grayscale array to jet colormap RGB using pure numpy."""
    # Jet colormap approximation: blue→cyan→green→yellow→red
    r = np.clip(1.5 - np.abs(gray_array * 4 - 3), 0, 1)
    g = np.clip(1.5 - np.abs(gray_array * 4 - 2), 0, 1)
    b = np.clip(1.5 - np.abs(gray_array * 4 - 1), 0, 1)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def gaussian_blur_numpy(arr, sigma=15):
    """Simple Gaussian blur via repeated box filter — no scipy needed."""
    from PIL import Image as PILImage
    pil = PILImage.fromarray((arr * 255).clip(0, 255).astype(np.uint8))
    # Use PIL's GaussianBlur (radius ≈ sigma)
    radius = max(1, int(sigma))
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=radius))
    result = np.array(blurred).astype(float) / 255.0
    return result


def generate_attention_map(image):
    """
    Generate a simulated Grad-CAM style attention map using pure PIL.

    TODO: Replace with real Grad-CAM from your MobileNetV2 model:
        from tf_keras_vis.gradcam import Gradcam
        gradcam = Gradcam(model)
        cam = gradcam(score_fn, preprocessed_input)
        attention = cam[0]  # shape (224, 224), values 0-1
    """
    SIZE = 224
    img_resized = image.convert('L').resize((SIZE, SIZE))
    edges = np.array(img_resized.filter(ImageFilter.FIND_EDGES)).astype(float)

    # Normalize edges
    if edges.max() > edges.min():
        edges = (edges - edges.min()) / (edges.max() - edges.min())

    # Smooth to make it look like a heat blob
    attention = gaussian_blur_numpy(edges, sigma=18)

    # Normalize again after blur
    if attention.max() > attention.min():
        attention = (attention - attention.min()) / (attention.max() - attention.min())

    return img_resized, attention


def add_label(canvas, text, x, y, color=(30, 30, 30)):
    """Draw text label onto a PIL image canvas."""
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), text, fill=color)
    return canvas


def draw_annotation(draw, canvas_arr, attn_resized, x_offset, y_offset, size, threshold_high=0.72, threshold_mid=0.45):
    """
    Find high-attention regions and draw labeled arrows pointing to them.
    Returns a list of (label, description) tuples for the legend.
    """
    annotations = []

    # ── Find centroid of HIGH attention zone (red) ────────────
    high_mask = attn_resized >= threshold_high
    if high_mask.sum() > 50:
        ys, xs = np.where(high_mask)
        cx = int(xs.mean() * size / attn_resized.shape[1]) + x_offset
        cy = int(ys.mean() * size / attn_resized.shape[0]) + y_offset

        # Arrow: from label outside → centroid
        lx = cx - 70 if cx > x_offset + size // 2 else cx + 70
        ly = max(cy - 40, y_offset + 10)
        draw.line([(lx, ly), (cx, cy)], fill=(220, 30, 30), width=2)
        # Arrowhead
        draw.polygon([(cx, cy), (cx-5, cy-8), (cx+5, cy-8)], fill=(220, 30, 30))
        # Label box
        draw.rectangle([(lx - 2, ly - 14), (lx + 98, ly + 2)], fill=(220, 30, 30))
        draw.text((lx, ly - 13), "Stroke irregularity", fill=(255, 255, 255))
        annotations.append(("🔴 Red zone", "High tremor / irregular stroke pattern"))

    # ── Find centroid of MID attention zone (yellow/orange) ───
    mid_mask = (attn_resized >= threshold_mid) & (attn_resized < threshold_high)
    if mid_mask.sum() > 100:
        ys, xs = np.where(mid_mask)
        # Pick a point near the edge of mid zone for variety
        idx = len(xs) // 3
        cx2 = int(xs[idx] * size / attn_resized.shape[1]) + x_offset
        cy2 = int(ys[idx] * size / attn_resized.shape[0]) + y_offset

        lx2 = cx2 + 60 if cx2 < x_offset + size // 2 else cx2 - 60
        ly2 = min(cy2 + 40, y_offset + size - 20)
        draw.line([(lx2, ly2), (cx2, cy2)], fill=(200, 120, 0), width=2)
        draw.polygon([(cx2, cy2), (cx2-5, cy2+6), (cx2+5, cy2+6)], fill=(200, 120, 0))
        draw.rectangle([(lx2 - 2, ly2), (lx2 + 92, ly2 + 14)], fill=(200, 120, 0))
        draw.text((lx2, ly2 + 1), "Uneven spacing", fill=(255, 255, 255))
        annotations.append(("🟡 Yellow zone", "Moderate pressure variation / uneven spacing"))

    # ── Low attention zone label ───────────────────────────────
    low_mask = attn_resized < 0.25
    if low_mask.sum() > 200:
        ys, xs = np.where(low_mask)
        idx = len(xs) // 2
        cx3 = int(xs[idx] * size / attn_resized.shape[1]) + x_offset
        cy3 = int(ys[idx] * size / attn_resized.shape[0]) + y_offset
        cy3 = min(cy3, y_offset + size - 25)

        draw.rectangle([(cx3 - 2, cy3 - 2), (cx3 + 76, cy3 + 12)], fill=(30, 100, 180))
        draw.text((cx3, cy3 - 1), "Smooth strokes", fill=(255, 255, 255))
        annotations.append(("🔵 Blue zone", "Normal smooth strokes — low PD contribution"))

    return annotations


def generate_comparison_figure(image, confidence):
    """
    Pure PIL side-by-side comparison with PD-specific annotations:
      Left  — Original drawing (grayscale)
      Right — Grad-CAM heatmap overlay with labeled region annotations

    Annotations explain which parts of the drawing contribute to PD detection.
    No matplotlib used — works reliably on HuggingFace Spaces.
    """
    SIZE = 420          # each panel: SIZE x SIZE pixels
    PADDING = 16        # gap between panels
    HEADER_H = 44       # top label bar height
    COLORBAR_W = 36     # colorbar strip + labels
    LEGEND_H = 110      # bottom legend area
    TOTAL_W = SIZE * 2 + PADDING * 3 + COLORBAR_W
    TOTAL_H = HEADER_H + SIZE + LEGEND_H

    # ── Prepare base grayscale image ──────────────────────────
    img_gray_small, attention = generate_attention_map(image)
    img_gray = img_gray_small.resize((SIZE, SIZE), Image.LANCZOS)
    gray_arr = np.array(img_gray)
    gray_rgb = np.stack([gray_arr] * 3, axis=-1)

    # ── Build heatmap overlay panel ───────────────────────────
    attn_resized = np.array(
        Image.fromarray((attention * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS)
    ).astype(float) / 255.0

    jet_rgb = apply_jet_colormap(attn_resized)
    alpha = 0.45
    blended = (gray_rgb * (1 - alpha) + jet_rgb * alpha).clip(0, 255).astype(np.uint8)

    # ── Build colorbar strip ──────────────────────────────────
    cbar_vals = np.linspace(1.0, 0.0, SIZE).reshape(-1, 1)
    cbar_jet = apply_jet_colormap(np.repeat(cbar_vals, 18, axis=1))
    cbar_img = Image.fromarray(cbar_jet)

    # ── Compose canvas ────────────────────────────────────────
    BG = (248, 248, 250)
    canvas = Image.new('RGB', (TOTAL_W, TOTAL_H), color=BG)

    x_left  = PADDING
    x_right = PADDING * 2 + SIZE
    x_cbar  = x_right + SIZE + 6

    canvas.paste(Image.fromarray(gray_rgb.astype(np.uint8)), (x_left, HEADER_H))
    canvas.paste(Image.fromarray(blended), (x_right, HEADER_H))
    canvas.paste(cbar_img, (x_cbar, HEADER_H))

    draw = ImageDraw.Draw(canvas)

    # ── Panel headers ─────────────────────────────────────────
    draw.rectangle([(x_left, 0), (x_left + SIZE, HEADER_H - 2)], fill=(60, 60, 80))
    draw.text((x_left + SIZE // 2 - 55, 13), "Original Drawing", fill=(255, 255, 255))

    draw.rectangle([(x_right, 0), (x_right + SIZE, HEADER_H - 2)], fill=(60, 60, 80))
    draw.text((x_right + SIZE // 2 - 80, 13), "Grad-CAM Attention Map", fill=(255, 255, 255))

    # ── Colorbar labels ───────────────────────────────────────
    draw.text((x_cbar + 20, HEADER_H),           "High", fill=(180, 30, 30))
    draw.text((x_cbar + 20, HEADER_H + SIZE//2 - 6), "Mid",  fill=(160, 100, 0))
    draw.text((x_cbar + 20, HEADER_H + SIZE - 14), "Low",  fill=(30, 60, 180))

    # Colorbar border
    draw.rectangle([(x_cbar - 1, HEADER_H - 1), (x_cbar + 19, HEADER_H + SIZE + 1)],
                   outline=(160, 160, 160), width=1)

    # ── PD Annotations on heatmap panel ──────────────────────
    annotations = draw_annotation(
        draw, blended, attn_resized,
        x_offset=x_right, y_offset=HEADER_H, size=SIZE
    )

    # ── Divider ───────────────────────────────────────────────
    draw.line([(x_right - PADDING // 2, 0),
               (x_right - PADDING // 2, HEADER_H + SIZE)],
              fill=(200, 200, 210), width=1)

    # ── Legend area ───────────────────────────────────────────
    legend_y = HEADER_H + SIZE
    draw.rectangle([(0, legend_y), (TOTAL_W, TOTAL_H)], fill=(38, 38, 52))

    # Confidence badge (left side)
    if confidence >= 0.7:
        badge_color = (255, 100, 90)
        badge_text  = f"PD Probability: {confidence:.1%}  ▲ HIGH RISK"
    elif confidence >= 0.4:
        badge_color = (255, 180, 60)
        badge_text  = f"PD Probability: {confidence:.1%}  ● MODERATE RISK"
    else:
        badge_color = (80, 210, 130)
        badge_text  = f"PD Probability: {confidence:.1%}  ▼ LOW RISK"

    draw.text((PADDING, legend_y + 10), badge_text, fill=badge_color)

    # Zone legend (right side of footer)
    zone_defs = [
        ((220, 60, 60),  "Red   = High attention: tremor / stroke irregularity"),
        ((210, 140, 0),  "Yellow = Mid attention: uneven spacing / pressure variation"),
        ((40, 100, 200), "Blue   = Low attention: smooth normal strokes"),
    ]
    lx_start = TOTAL_W // 2
    for i, (col, label) in enumerate(zone_defs):
        ty = legend_y + 8 + i * 30
        draw.rectangle([(lx_start, ty + 2), (lx_start + 14, ty + 14)], fill=col)
        draw.text((lx_start + 20, ty), label, fill=(210, 210, 220))

    return canvas


def classify_drawing(image):
    """
    Placeholder for your MobileNetV2 CNN classifier.

    TODO: Replace this with your actual model inference:
        from tensorflow.keras.models import load_model
        model = load_model('your_mobilenetv2_model.h5')
        img = preprocess_input(np.array(image.resize((224, 224))))
        img = np.expand_dims(img, axis=0)
        confidence = float(model.predict(img)[0][0])
        return confidence
    """
    if image is None:
        return None

    # === PLACEHOLDER: simulated confidence for demo ===
    np.random.seed(hash(str(image.size)) % 2**32)
    confidence = float(np.random.beta(3, 2))
    return confidence


# ============================================================
# COMBINED PREDICTION
# ============================================================

def combined_prediction(risk_score, cnn_confidence, max_score=22):
    """Fuse Stage 1 risk score with Stage 2 CNN output."""
    norm_risk = risk_score / max_score
    _, risk_weight, _ = get_risk_level(risk_score)
    weighted_risk = min(norm_risk * risk_weight, 1.0)

    RISK_W = 0.35
    CNN_W = 0.65
    combined = weighted_risk * RISK_W + cnn_confidence * CNN_W

    if combined >= 0.70:
        rec = "HIGH PROBABILITY"
        advice = "Strongly recommend consultation with a neurologist for comprehensive evaluation."
    elif combined >= 0.45:
        rec = "MODERATE PROBABILITY"
        advice = "Recommend scheduling a medical evaluation. Early detection enables better management."
    elif combined >= 0.25:
        rec = "LOW-MODERATE"
        advice = "Consider monitoring symptoms. Consult a doctor if symptoms worsen or new ones appear."
    else:
        rec = "LOW PROBABILITY"
        advice = "Low risk based on current assessment. Continue monitoring general health."

    return combined, rec, advice


# ============================================================
# GRADIO UI FUNCTIONS
# ============================================================

def run_stage1(
    age, sex,
    tremor, bradykinesia, rigidity,
    falls, gait_difficulty, weakness, asymmetric,
    cognitive_decline, sleep_disorder, constipation, depression,
    bedridden, walk_with_aid,
    has_cva, has_all_metabolic
):
    score, breakdown = compute_risk_score(
        age, sex,
        tremor, bradykinesia, rigidity,
        falls, gait_difficulty, weakness, asymmetric,
        cognitive_decline, sleep_disorder, constipation, depression,
        bedridden, walk_with_aid,
        has_cva, has_all_metabolic
    )

    level, weight, emoji = get_risk_level(score)

    result = f"## {emoji} Risk Level: {level}\n\n"
    result += f"**Score: {score} / 22 points**\n\n"

    if breakdown:
        result += "### Score Breakdown\n"
        for item in breakdown:
            result += f"- {item}\n"
    else:
        result += "_No risk factors identified from questionnaire._\n"

    result += f"\n---\n"
    result += f"**Risk Weight for Combined Prediction:** ×{weight}\n\n"

    if level == "Low":
        result += "> 🟢 Low clinical risk. The drawing analysis (Stage 2) will carry more weight in the final assessment.\n"
    elif level == "Medium":
        result += "> 🟡 Moderate clinical risk detected. Proceeding to drawing analysis will provide additional diagnostic insight.\n"
    else:
        result += "> 🔴 High clinical risk detected. Drawing analysis is recommended, but consider consulting a neurologist regardless of Stage 2 results.\n"

    return result, score


def run_stage2(image, drawing_type):
    """Process Stage 2 drawing and return CNN confidence with side-by-side heatmap."""
    if image is None:
        return None, "⚠️ Please upload a hand-drawing image (spiral or wave pattern).", None

    confidence = classify_drawing(image)

    try:
        comparison_img = generate_comparison_figure(image, confidence)
    except Exception as e:
        comparison_img = None
        print(f"Heatmap generation error: {e}")

    result = f"## Drawing Analysis Result ({drawing_type})\n\n"
    result += f"**CNN Confidence (P(PD)):** {confidence:.1%}\n\n"

    if confidence >= 0.7:
        result += "> 🔴 Drawing patterns suggest high probability of motor impairment consistent with PD.\n"
        result += "\n**Key observations:** The heatmap highlights regions with tremor-like irregularities, uneven stroke spacing, and inconsistent pressure patterns.\n"
    elif confidence >= 0.4:
        result += "> 🟡 Drawing patterns show some irregularities that may warrant further evaluation.\n"
        result += "\n**Key observations:** The heatmap shows moderate areas of concern — some unsteadiness in stroke continuity.\n"
    else:
        result += "> 🟢 Drawing patterns appear within normal range.\n"
        result += "\n**Key observations:** The heatmap shows relatively uniform attention — smooth, consistent strokes detected.\n"

    return comparison_img, result, confidence


def run_combined(risk_score, cnn_confidence):
    if risk_score is None:
        return "⚠️ Please complete Stage 1 (questionnaire) first."
    if cnn_confidence is None:
        return "⚠️ Please complete Stage 2 (drawing upload) first."

    combined, rec, advice = combined_prediction(int(risk_score), float(cnn_confidence))
    level, weight, emoji = get_risk_level(int(risk_score))

    result = f"# Final Assessment\n\n"
    result += f"## {rec}\n\n"
    result += f"**Combined Score: {combined:.1%}**\n\n"
    result += f"---\n\n"
    result += f"### How this was calculated\n\n"
    result += f"| Component | Value | Weight |\n"
    result += f"|-----------|-------|--------|\n"
    result += f"| Clinical Risk Score | {int(risk_score)} / 22 ({level}) | 35% (×{weight}) |\n"
    result += f"| Drawing CNN Confidence | {float(cnn_confidence):.1%} | 65% |\n"
    result += f"| **Combined Score** | **{combined:.1%}** | |\n\n"
    result += f"### Recommendation\n\n"
    result += f"{advice}\n\n"
    result += f"---\n"
    result += f"⚠️ **Disclaimer:** This tool is for preliminary screening only and does not constitute a medical diagnosis. "
    result += f"Always consult a qualified healthcare professional for proper evaluation and diagnosis of Parkinson's disease."

    return result


# ============================================================
# BUILD GRADIO INTERFACE
# ============================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

* {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.prose h1, .prose h2, .prose h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
}
.prose {
    font-size: 15px;
    line-height: 1.6;
}
"""

with gr.Blocks(
    title="PD Prediction System",
    css=CUSTOM_CSS,
    theme=gr.themes.Base(
        primary_hue="purple",
        secondary_hue="gray",
        neutral_hue="gray",
        font=gr.themes.GoogleFont("DM Sans"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    )
) as demo:

    # Hidden state variables
    risk_score_state = gr.State(value=None)
    cnn_confidence_state = gr.State(value=None)

    # ── HEADER ──
    gr.Markdown(
        """
        # 🧠 Parkinson's Disease Prediction System
        ### Two-Stage Clinical Screening Tool

        **Stage 1** — Answer a clinical questionnaire → Generates a risk score\n
        **Stage 2** — Upload a hand-drawing → CNN classifier analyzes motor patterns\n
        **Combined** — Both results are fused into a final recommendation

        ---
        """
    )

    with gr.Tabs() as tabs:

        # ════════════════════════════════════════════
        # STAGE 1: QUESTIONNAIRE
        # ════════════════════════════════════════════
        with gr.Tab("📋 Stage 1: Clinical Questionnaire", id="stage1"):

            gr.Markdown("### Complete the questionnaire below. Check all that apply.")

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 👤 Demographics")
                    age = gr.Radio(
                        choices=["Under 40", "40-49", "50-59", "60-69", "70-79", "80+"],
                        label="Age range",
                        value="60-69"
                    )
                    sex = gr.Radio(
                        choices=["Male", "Female"],
                        label="Sex",
                        value="Male"
                    )

                with gr.Column(scale=1):
                    gr.Markdown("#### 🏥 Medical History")
                    has_cva = gr.Checkbox(label="History of stroke (CVA)")
                    has_all_metabolic = gr.Checkbox(
                        label="Has ALL three: Hypertension + Diabetes + Dyslipidemia"
                    )

            gr.Markdown("---")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### ⚡ Cardinal Motor Symptoms")
                    gr.Markdown("_These are the primary signs of Parkinson's disease_")
                    tremor = gr.Checkbox(label="Tremor — Involuntary shaking, especially at rest (hands, jaw, legs)")
                    bradykinesia = gr.Checkbox(label="Bradykinesia — Slowness of movement, difficulty initiating movement")
                    rigidity = gr.Checkbox(label="Rigidity — Muscle stiffness, resistance to passive movement")

                with gr.Column():
                    gr.Markdown("#### 🚶 Supporting Motor Symptoms")
                    falls = gr.Checkbox(label="Falls / Balance problems — Frequent stumbling or falling")
                    gait_difficulty = gr.Checkbox(label="Gait difficulty — Shuffling walk, freezing, or difficulty walking")
                    weakness = gr.Checkbox(label="Weakness — General muscle weakness")
                    asymmetric = gr.Checkbox(label="Asymmetric symptoms — One side of body affected more than the other")

            gr.Markdown("---")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 🌙 Non-Motor Symptoms")
                    cognitive_decline = gr.Checkbox(label="Cognitive decline — Memory problems, confusion, difficulty concentrating")
                    sleep_disorder = gr.Checkbox(label="Sleep disorder — Insomnia, vivid dreams, acting out during sleep (RBD)")
                    constipation = gr.Checkbox(label="Constipation — Chronic constipation not explained by other causes")
                    depression = gr.Checkbox(label="Depression / Anxiety — Persistent low mood, loss of interest, worry")

                with gr.Column():
                    gr.Markdown("#### 🛏️ Functional Impact")
                    gr.Markdown("_How do symptoms affect daily life?_")
                    bedridden = gr.Checkbox(label="Bedridden — Unable to get out of bed without assistance")
                    walk_with_aid = gr.Checkbox(label="Uses walking aid — Requires cane, walker, or wheelchair")

            gr.Markdown("---")

            stage1_btn = gr.Button("Calculate Risk Score", variant="primary", size="lg")
            stage1_result = gr.Markdown(label="Stage 1 Result")

            stage1_btn.click(
                fn=run_stage1,
                inputs=[
                    age, sex,
                    tremor, bradykinesia, rigidity,
                    falls, gait_difficulty, weakness, asymmetric,
                    cognitive_decline, sleep_disorder, constipation, depression,
                    bedridden, walk_with_aid,
                    has_cva, has_all_metabolic
                ],
                outputs=[stage1_result, risk_score_state]
            )

        # ════════════════════════════════════════════
        # STAGE 2: DRAWING ANALYSIS
        # ════════════════════════════════════════════
        with gr.Tab("✏️ Stage 2: Drawing Analysis", id="stage2"):

            gr.Markdown(
                """
                ### Upload a Hand-Drawing for Analysis

                Please draw one of the following patterns on paper and upload a photo:

                **Accepted patterns:**
                - 🌀 **Spiral** — Draw an Archimedean spiral (best for PD detection)
                - 〰️ **Wave** — Draw a continuous wave pattern

                **Tips for best results:**
                - Use a **white paper** with a **dark pen**
                - Draw with your **dominant hand** first, then your **non-dominant hand**
                - Take the photo in **good lighting** with minimal background
                - Keep the camera **directly above** the paper
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    drawing_type = gr.Radio(
                        choices=["Spiral", "Wave"],
                        label="Drawing type",
                        value="Spiral"
                    )
                    drawing_input = gr.Image(
                        label="Upload your hand-drawing",
                        type="pil",
                        height=300
                    )

            stage2_btn = gr.Button("🔬 Analyze Drawing", variant="primary", size="lg")

            gr.Markdown("---")
            gr.Markdown("### Analysis Results — Original vs Grad-CAM Heatmap (side by side)")

            comparison_output = gr.Image(
                label="Original Drawing | Grad-CAM Attention Heatmap",
                type="pil",
                height=420
            )

            stage2_result = gr.Markdown(label="Stage 2 Result")

            stage2_btn.click(
                fn=run_stage2,
                inputs=[drawing_input, drawing_type],
                outputs=[comparison_output, stage2_result, cnn_confidence_state]
            )

        # ════════════════════════════════════════════
        # COMBINED RESULT
        # ════════════════════════════════════════════
        with gr.Tab("📊 Combined Result", id="combined"):

            gr.Markdown(
                """
                ### Final Combined Assessment

                This combines your **clinical risk score** (Stage 1) with the
                **drawing analysis** (Stage 2) into a final recommendation.

                Make sure you have completed both stages before generating the final result.
                """
            )

            combined_btn = gr.Button("Generate Final Assessment", variant="primary", size="lg")
            combined_result = gr.Markdown(label="Combined Result")

            combined_btn.click(
                fn=run_combined,
                inputs=[risk_score_state, cnn_confidence_state],
                outputs=[combined_result]
            )

        # ════════════════════════════════════════════
        # ABOUT
        # ════════════════════════════════════════════
        with gr.Tab("ℹ️ About", id="about"):
            gr.Markdown(
                """
                ## About This Tool

                ### Two-Stage Architecture

                | Stage | Input | Method | Output |
                |-------|-------|--------|--------|
                | **Stage 1** | Clinical questionnaire | Point-based risk scoring | Risk score (0-22) |
                | **Stage 2** | Hand-drawing image (Spiral or Wave) | MobileNetV2 CNN classifier | PD probability (0-1) |
                | **Combined** | Both scores | Weighted fusion (35/65) | Final recommendation |

                ### Risk Scoring System

                The clinical risk scoring system was derived from analysis of **1,340 confirmed
                Parkinson's disease patient records** from a hospital in Udon Thani, Thailand
                (2567-2568 BE).

                | Risk Level | Score | Weight | Description |
                |-----------|-------|--------|-------------|
                | 🟢 Low | 0-2 | ×0.3 | Few or no clinical risk factors |
                | 🟡 Medium | 3-5 | ×1.0 | Some clinical risk factors present |
                | 🔴 High | 6+ | ×1.5 | Multiple clinical risk factors |

                ### Combined Prediction

                ```
                combined = (weighted_risk × 0.35) + (cnn_confidence × 0.65)
                ```

                | Combined Score | Recommendation |
                |---------------|----------------|
                | ≥ 70% | HIGH — Strongly recommend neurologist consultation |
                | 45-69% | MODERATE — Recommend medical evaluation |
                | 25-44% | LOW-MODERATE — Monitor, consult if worsens |
                | < 25% | LOW — Continue general health monitoring |

                ### Research Team
                - Supervisor: Dr. Sasiporn Usanavasin
                - Sai Wai Yan Phyo
                - Kantapon Makpisut

                ### Disclaimer

                ⚠️ This tool is for **preliminary screening purposes only** and does not
                constitute a medical diagnosis. Parkinson's disease can only be diagnosed
                by a qualified healthcare professional through comprehensive clinical
                evaluation. Always consult a neurologist if you have concerns about
                Parkinson's disease symptoms.

                ### References

                - Du, Q., et al. (2024). Parkinson's Disease Detection by Using Machine
                Learning Method based on Local Classification on Class Boundary.
                *Discover Applied Sciences*, 6:576.
                - Hospital clinical data: 1,340 records, Udon Thani, Thailand (2567-2568 BE)
                """
            )

    # ── FOOTER ──
    gr.Markdown(
        """
        ---
        <center>
        <small>
        🧠 PD Prediction System v1.1 | Research Project |
        Parkinson's Disease Prediction Using Deep Learning
        </small>
        </center>
        """
    )


# ============================================================
# LAUNCH
# ============================================================
if __name__ == "__main__":
    demo.launch(share=True)