import gradio as gr
import numpy as np
import tensorflow as tf
import matplotlib.cm as cm
from tensorflow.keras.models import load_model
from huggingface_hub import hf_hub_download

# Download models from HF
spiral_path = hf_hub_download(
    repo_id="your-username/parkinsons-detection",
    filename="spiral_mobilenetv2.keras"
)
wave_path = hf_hub_download(
    repo_id="your-username/parkinsons-detection",
    filename="wave_mobilenetv2.keras"
)

spiral_model = load_model(spiral_path)
wave_model = load_model(wave_path)

THRESHOLDS = {'Spiral': 0.35, 'Wave': 0.50}

def predict_and_gradcam(img, drawing_type):
    model = spiral_model if drawing_type == 'Spiral' else wave_model
    threshold = THRESHOLDS[drawing_type]

    img_resized = img.resize((224, 224))
    img_array = np.array(img_resized) / 255.0

    if img_array.ndim == 2:
        img_array = np.stack([img_array]*3, axis=-1)
    elif img_array.shape[-1] == 4:
        img_array = img_array[:, :, :3]

    img_array_exp = np.expand_dims(img_array, axis=0)

    pred = model.predict(img_array_exp, verbose=0)[0][0]
    label = 'Parkinson' if pred > threshold else 'Healthy'
    confidence = pred if pred > threshold else 1 - pred

    # Grad-CAM
    grad_model = tf.keras.models.Model(
        inputs=model.input,
        outputs=[model.get_layer('Conv_1').output, model.output]
    )
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array_exp)
        loss = predictions[:, 0]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = conv_outputs[0] @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    heatmap = heatmap.numpy()

    heatmap_colored = cm.jet(np.uint8(255 * heatmap))[:, :, :3]
    heatmap_colored = tf.image.resize(heatmap_colored, (224, 224)).numpy()
    superimposed = np.clip(heatmap_colored * 0.4 + img_array, 0, 1)

    result = f"Prediction: {label}\nConfidence: {confidence:.1%}\nDrawing Type: {drawing_type}"
    return superimposed, result

with gr.Blocks(title="Parkinson's Disease Detection") as demo:
    gr.Markdown("# 🧠 Parkinson's Disease Detection")
    gr.Markdown("Upload a hand drawing (spiral or wave) to predict Parkinson's disease risk.")

    with gr.Row():
        with gr.Column():
            img_input = gr.Image(type='pil', label="Upload Drawing")
            drawing_type = gr.Radio(
                choices=['Spiral', 'Wave'],
                value='Spiral',
                label="Drawing Type"
            )
            submit_btn = gr.Button("Predict", variant="primary")
        with gr.Column():
            gradcam_output = gr.Image(label="Grad-CAM Heatmap")
            result_output = gr.Textbox(label="Result", lines=3)

    submit_btn.click(
        fn=predict_and_gradcam,
        inputs=[img_input, drawing_type],
        outputs=[gradcam_output, result_output]
    )
    gr.Markdown("⚠️ *Research purposes only. Not a clinical diagnostic tool.*")

demo.launch()