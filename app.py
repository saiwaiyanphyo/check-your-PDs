"""
🧠 Parkinson's Disease Prediction System
Two-Stage: Clinical Risk Scoring + Hand-Drawing Classification

Stage 1: Clinical questionnaire → Risk score (0-22 points)
Stage 2: Hand-drawing upload → CNN classifier (PD vs Healthy)
Combined: Weighted fusion → Final recommendation

Derived from 1,340 hospital records (Udon Thani, Thailand)
"""

import gradio as gr
import numpy as np
from PIL import Image

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
# ============================================================

def generate_heatmap(image):
    """
    Generate a Grad-CAM style heatmap overlay on the drawing.

    TODO: Replace with real Grad-CAM from your CNN model:
        from tf_keras_vis.gradcam import Gradcam
        gradcam = Gradcam(model)
        cam = gradcam(score, seed_input)
        heatmap = np.uint8(255 * cam)

    This placeholder generates a simulated attention heatmap
    based on edge density (areas with more drawing strokes).
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import ImageFilter

    img_array = np.array(image.convert('L').resize((224, 224)))

    # Simulate attention: use edge detection as proxy for stroke density
    edges = np.array(image.convert('L').resize((224, 224)).filter(ImageFilter.FIND_EDGES))
    from scipy.ndimage import gaussian_filter
    attention = gaussian_filter(edges.astype(float), sigma=15)
    attention = (attention - attention.min()) / (attention.max() - attention.min() + 1e-8)

    # Create heatmap overlay figure
    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
    ax.imshow(img_array, cmap='gray', alpha=0.6)
    heatmap = ax.imshow(attention, cmap='jet', alpha=0.5, vmin=0, vmax=1)
    plt.colorbar(heatmap, ax=ax, fraction=0.046, pad=0.04, label='Attention intensity')
    ax.set_title('Model attention heatmap', fontsize=13, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()

    # Convert figure to PIL image
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    heatmap_img = Image.fromarray(buf[:, :, :3])
    plt.close(fig)

    return heatmap_img


def generate_comparison_figure(image, confidence):
    """Create a side-by-side comparison: original vs heatmap with results."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import ImageFilter

    img_resized = image.convert('L').resize((224, 224))
    img_array = np.array(img_resized)

    # Generate attention map
    edges = np.array(img_resized.filter(ImageFilter.FIND_EDGES))
    from scipy.ndimage import gaussian_filter
    attention = gaussian_filter(edges.astype(float), sigma=15)
    attention = (attention - attention.min()) / (attention.max() - attention.min() + 1e-8)

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), gridspec_kw={'width_ratios': [1, 1, 0.4]})

    # Panel 1: Original drawing
    axes[0].imshow(img_array, cmap='gray')
    axes[0].set_title('Original drawing', fontsize=14, fontweight='bold')
    axes[0].axis('off')

    # Panel 2: Heatmap overlay
    axes[1].imshow(img_array, cmap='gray', alpha=0.6)
    hm = axes[1].imshow(attention, cmap='jet', alpha=0.5, vmin=0, vmax=1)
    axes[1].set_title('Model attention heatmap', fontsize=14, fontweight='bold')
    axes[1].axis('off')
    plt.colorbar(hm, ax=axes[1], fraction=0.046, pad=0.04)

    # Panel 3: Result gauge
    axes[2].axis('off')
    if confidence >= 0.7:
        color = '#e74c3c'
        label = 'HIGH'
    elif confidence >= 0.4:
        color = '#f39c12'
        label = 'MODERATE'
    else:
        color = '#27ae60'
        label = 'LOW'

    # Draw gauge
    theta = np.linspace(np.pi, 0, 100)
    axes[2].plot(np.cos(theta), np.sin(theta), 'k-', linewidth=3, alpha=0.2)

    # Fill arc based on confidence
    n_fill = int(confidence * 100)
    for i in range(n_fill):
        t = np.pi - (i / 100) * np.pi
        r_color = plt.cm.RdYlGn_r(i / 100)
        axes[2].plot(np.cos(t), np.sin(t), '.', color=r_color, markersize=8)

    # Needle
    needle_angle = np.pi - confidence * np.pi
    axes[2].plot([0, 0.7 * np.cos(needle_angle)], [0, 0.7 * np.sin(needle_angle)],
                 'k-', linewidth=2.5)
    axes[2].plot(0, 0, 'ko', markersize=8)

    axes[2].set_xlim(-1.3, 1.3)
    axes[2].set_ylim(-0.3, 1.3)
    axes[2].text(0, -0.15, f'{confidence:.1%}', ha='center', fontsize=22, fontweight='bold', color=color)
    axes[2].text(0, -0.28, label, ha='center', fontsize=13, fontweight='bold', color=color)
    axes[2].text(-1.1, 0, '0%', fontsize=9, color='#27ae60', fontweight='bold')
    axes[2].text(0.9, 0, '100%', fontsize=9, color='#e74c3c', fontweight='bold')
    axes[2].set_title('PD probability', fontsize=14, fontweight='bold')

    plt.suptitle('Drawing Analysis — Stage 2', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    # Convert to PIL
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    result_img = Image.fromarray(buf[:, :, :3])
    plt.close(fig)

    return result_img


def classify_drawing(image):
    """
    Placeholder for your CNN classifier.

    TODO: Replace this with your actual model inference:
      - Load your trained model (VGG19 / ResNet50 / CNN-BLSTM)
      - Preprocess the image (grayscale, normalize, resize)
      - Return P(PD) confidence between 0 and 1

    Example with a real model:
        from tensorflow.keras.models import load_model
        model = load_model('your_model.h5')
        img = preprocess(image)
        confidence = model.predict(img)[0][0]
        return float(confidence)
    """
    if image is None:
        return None

    # === PLACEHOLDER: Random confidence for demo ===
    # Replace this entire block with your real model
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
        color = "red"
        advice = "Strongly recommend consultation with a neurologist for comprehensive evaluation."
    elif combined >= 0.45:
        rec = "MODERATE PROBABILITY"
        color = "orange"
        advice = "Recommend scheduling a medical evaluation. Early detection enables better management."
    elif combined >= 0.25:
        rec = "LOW-MODERATE"
        color = "goldenrod"
        advice = "Consider monitoring symptoms. Consult a doctor if symptoms worsen or new ones appear."
    else:
        rec = "LOW PROBABILITY"
        color = "green"
        advice = "Low risk based on current assessment. Continue monitoring general health."

    return combined, rec, color, advice


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
    """Process Stage 1 questionnaire and return risk assessment."""
    score, breakdown = compute_risk_score(
        age, sex,
        tremor, bradykinesia, rigidity,
        falls, gait_difficulty, weakness, asymmetric,
        cognitive_decline, sleep_disorder, constipation, depression,
        bedridden, walk_with_aid,
        has_cva, has_all_metabolic
    )

    level, weight, emoji = get_risk_level(score)

    # Build result text
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


def run_stage2(image):
    """Process Stage 2 drawing and return CNN confidence with heatmap comparison."""
    if image is None:
        return None, "⚠️ Please upload a hand-drawing image (spiral, wave, or square pattern).", None

    confidence = classify_drawing(image)
    comparison_img = generate_comparison_figure(image, confidence)

    result = f"## Drawing Analysis Result\n\n"
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
    """Combine both stages into final prediction."""
    if risk_score is None:
        return "⚠️ Please complete Stage 1 (questionnaire) first."
    if cnn_confidence is None:
        return "⚠️ Please complete Stage 2 (drawing upload) first."

    combined, rec, color, advice = combined_prediction(int(risk_score), float(cnn_confidence))
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

            stage1_btn = gr.Button("🔍 Calculate Risk Score", variant="primary", size="lg")
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

                **Recommended patterns:**
                - 🌀 **Spiral** — Draw an Archimedean spiral (best for PD detection)
                - 〰️ **Wave** — Draw a continuous wave pattern
                - ⬜ **Square/Circle** — Draw geometric shapes

                **Tips for best results:**
                - Use a **white paper** with a **dark pen**
                - Draw with your **dominant hand** first, then your **non-dominant hand**
                - Take the photo in **good lighting** with minimal background
                - Keep the camera **directly above** the paper
                """
            )

            with gr.Row():
                drawing_input = gr.Image(
                    label="Upload your hand-drawing",
                    type="pil",
                    height=300
                )

            stage2_btn = gr.Button("🔬 Analyze Drawing", variant="primary", size="lg")

            gr.Markdown("---")
            gr.Markdown("### Analysis Results")

            comparison_output = gr.Image(
                label="Original vs Heatmap Comparison",
                type="pil",
                height=400
            )

            stage2_result = gr.Markdown(label="Stage 2 Result")

            stage2_btn.click(
                fn=run_stage2,
                inputs=[drawing_input],
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

            combined_btn = gr.Button("📊 Generate Final Assessment", variant="primary", size="lg")
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
                | **Stage 2** | Hand-drawing image | CNN classifier | PD probability (0-1) |
                | **Combined** | Both scores | Weighted fusion (35/65) | Final recommendation |

                ### Risk Scoring System

                The clinical risk scoring system was derived from analysis of **1,340 confirmed
                Parkinson's disease patient records** from a hospital in Udon Thani, Thailand
                (2567-2568 BE). Features were extracted from clinical notes using NLP techniques.

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
                - Sai Wai Yan Phyo (6722790282)
                - Kantapon Makpisut (6622781241)
                - Supervisor: Dr. Sasiporn Usanavasin

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
        🧠 PD Prediction System v1.0 | Research Project |
        Parkinson's Disease Prediction Using Deep Learning
        </small>
        </center>
        """
    )


# ============================================================
# LAUNCH
# ============================================================
if __name__ == "__main__":
    demo.launch()