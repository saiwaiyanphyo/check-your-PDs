"""
FastAPI backend for Parkinson's Disease Prediction System
Serves 3 endpoints:
  POST /stage1   — clinical questionnaire → risk score
  POST /stage2   — image upload → CNN confidence + heatmap
  POST /combined — fuse both → final recommendation
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import base64
import io
import os

from scoring import compute_risk_score, get_risk_level
from classifier import load_models, classify_drawing
from heatmap import generate_comparison_figure

app = FastAPI(title="PD Prediction API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Vercel domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once at startup
models = load_models()


# ── Stage 1 ──────────────────────────────────────────────────

class Stage1Input(BaseModel):
    age: str
    sex: str
    tremor: bool = False
    bradykinesia: bool = False
    rigidity: bool = False
    falls: bool = False
    gait_difficulty: bool = False
    weakness: bool = False
    asymmetric: bool = False
    cognitive_decline: bool = False
    sleep_disorder: bool = False
    constipation: bool = False
    depression: bool = False
    bedridden: bool = False
    walk_with_aid: bool = False
    has_cva: bool = False
    has_all_metabolic: bool = False


@app.post("/stage1")
def stage1(data: Stage1Input):
    score, breakdown = compute_risk_score(
        data.age, data.sex,
        data.tremor, data.bradykinesia, data.rigidity,
        data.falls, data.gait_difficulty, data.weakness, data.asymmetric,
        data.cognitive_decline, data.sleep_disorder, data.constipation, data.depression,
        data.bedridden, data.walk_with_aid,
        data.has_cva, data.has_all_metabolic,
    )
    level, weight, emoji = get_risk_level(score)
    return {
        "score": score,
        "max_score": 22,
        "level": level,
        "weight": weight,
        "emoji": emoji,
        "breakdown": breakdown,
    }


# ── Stage 2 ──────────────────────────────────────────────────

@app.post("/stage2")
async def stage2(
    file: UploadFile = File(...),
    drawing_type: str = Form(default="Spiral"),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/bmp"):
        raise HTTPException(400, "Unsupported image format. Use JPEG or PNG.")

    raw = await file.read()
    from PIL import Image
    image = Image.open(io.BytesIO(raw)).convert("RGB")

    model_key = drawing_type.lower()
    if model_key not in models:
        model_key = "spiral"

    confidence = classify_drawing(image, models[model_key])

    try:
        heatmap_img = generate_comparison_figure(image, confidence)
        buf = io.BytesIO()
        heatmap_img.save(buf, format="PNG")
        heatmap_b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print(f"Heatmap error: {e}")
        heatmap_b64 = None

    return {
        "confidence": round(confidence, 4),
        "drawing_type": drawing_type,
        "heatmap_base64": heatmap_b64,
    }


# ── Combined ─────────────────────────────────────────────────

class CombinedInput(BaseModel):
    risk_score: int
    cnn_confidence: float


@app.post("/combined")
def combined(data: CombinedInput):
    from scoring import combined_prediction
    combined_score, rec, advice = combined_prediction(data.risk_score, data.cnn_confidence)
    level, weight, emoji = get_risk_level(data.risk_score)
    return {
        "combined_score": round(combined_score, 4),
        "recommendation": rec,
        "advice": advice,
        "risk_level": level,
        "risk_weight": weight,
        "risk_emoji": emoji,
    }


@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": list(models.keys())}
