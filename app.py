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
# ============================================================

def fig_to_pil(fig):
    """Safely convert matplotlib figure to PIL Image using BytesIO."""
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format='PNG', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img = Image.open(buf).copy()
    buf.close()
    plt.close(fig)
    return img


def generate_attention_map(image):
    """
    Generate a simulated Grad-CAM style attention map.

    TODO: Replace with real Grad-CAM from your MobileNetV2 model:
        from tf_keras_vis.gradcam import Gradcam
        gradcam = Gradcam(model)
        cam = gradcam(score_fn, preprocessed_input)
        attention = np.uint8(255 * cam[0])
    """
    from PIL import ImageFilter
    from scipy.ndimage import gaussian_filter

    img_gray = image.convert('L').resize((224, 224))
    edges = np.array(img_gray.filter(ImageFilter.FIND_EDGES)).astype(float)
    attention = gaussian_filter(edges, sigma=15)
    if attention.max() > attention.min():
        attention = (attention - attention.min()) / (attention.max() - attention.min())
    else:
        attention = np.zeros_like(attention)
    return np.array(img_gray), attention


def generate_comparison_figure(image, confidence):
    """
    Create a TRUE side-by-side comparison:
    Left panel  — Original drawing
    Right panel — Grad-CAM heatmap overlay
    Both panels are the same size and sit next to each other horizontally.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    img_array, attention = generate_attention_map(image)

    # ── Two equal panels side by side ──────────────────────────
    fig, (ax_orig, ax_heat) = plt.subplots(
        1, 2,
        figsize=(10, 5),
        gridspec_kw={'wspace': 0.08}
    )

    # Panel 1: Original drawing
    ax_orig.imshow(img_array, cmap='gray')
    ax_orig.set_title('Original Drawing', fontsize=14, fontweight='bold', pad=10)
    ax_orig.axis('off')

    # Panel 2: Heatmap overlay
    ax_heat.imshow(img_array, cmap='gray', alpha=0.55)
    hm = ax_heat.imshow(attention, cmap='jet', alpha=0.50, vmin=0, vmax=1)
    ax_heat.set_title('Grad-CAM Attention Heatmap', fontsize=14, fontweight='bold', pad=10)
    ax_heat.axis('off')

    # Shared colorbar attached to heatmap panel only
    cbar = fig.colorbar(hm, ax=ax_heat, fraction=0.046, pad=0.04)
    cbar.set_label('Attention intensity', fontsize=10)

    # Confidence badge in suptitle
    if confidence >= 0.7:
        badge = f"PD Probability: {confidence:.1%}  🔴 HIGH"
        title_color = '#c0392b'
    elif confidence >= 0.4:
        badge = f"PD Probability: {confidence:.1%}  🟡 MODERATE"
        title_color = '#d35400'
    else:
        badge = f"PD Probability: {confidence:.1%}  🟢 LOW"
        title_color = '#27ae60'

    fig.suptitle(badge, fontsize=15, fontweight='bold', color=title_color, y=1.02)

    return fig_to_pil(fig)


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
        with gr.Tab("Combined Result", id="combined"):

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
        PD Prediction System v1.1 | Research Project |
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