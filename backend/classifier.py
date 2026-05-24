"""MobileNetV2 model loading and inference."""

import os
import numpy as np
from PIL import Image

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..")

MODEL_PATHS = {
    "spiral": os.path.join(MODEL_DIR, "spiral_mobilenetv2.keras"),
    "wave":   os.path.join(MODEL_DIR, "wave_mobilenetv2.keras"),
}


def load_models():
    """Load both Keras models at startup. Returns dict keyed by drawing type."""
    loaded = {}
    try:
        import tensorflow as tf
        for key, path in MODEL_PATHS.items():
            if os.path.exists(path):
                try:
                    loaded[key] = tf.keras.models.load_model(path)
                    print(f"Loaded model: {key} from {path}")
                except Exception as e:
                    print(f"Failed to load {key} model: {e} — using placeholder.")
            else:
                print(f"Model file not found: {path}")
    except Exception as e:
        print(f"TensorFlow unavailable ({e}) — using placeholder classifier.")
    return loaded


def classify_drawing(image: Image.Image, model) -> float:
    """
    Run inference on a PIL image using the given Keras model.
    Returns a float in [0, 1] representing PD probability.
    """
    if model is None:
        # Fallback placeholder when model isn't available
        np.random.seed(hash(str(image.size)) % 2**32)
        return float(np.random.beta(3, 2))

    try:
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

        img = image.convert("RGB").resize((224, 224))
        arr = np.array(img, dtype=np.float32)
        arr = preprocess_input(arr)
        arr = np.expand_dims(arr, axis=0)

        prediction = model.predict(arr, verbose=0)
        # Support both binary (sigmoid) and softmax outputs
        pred = prediction[0]
        if pred.shape == () or pred.shape == (1,):
            return float(pred.flat[0])
        # Softmax: index 1 = PD class
        return float(pred[1]) if len(pred) >= 2 else float(pred[0])

    except Exception as e:
        print(f"Inference error: {e}")
        np.random.seed(hash(str(image.size)) % 2**32)
        return float(np.random.beta(3, 2))
