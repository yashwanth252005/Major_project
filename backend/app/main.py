"""
FastAPI backend for the Brain Tumour Detection + Unified XAI dashboard.

Endpoints:
  GET  /health              -> liveness check + model status
  POST /predict              -> upload an MRI slice (png/jpg), get back
                                 { prediction, confidence, gradcam, lrp, shap }
                                 where the three XAI fields are base64 PNG
                                 heatmap overlays.
"""

import base64
import io
import logging
import os
import threading

import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from .config import IMG_SIZE, MAX_UPLOAD_BYTES, ALLOWED_IMAGE_EXTENSIONS, MAX_UPLOAD_MB
from .model import BrainTumorCNN
from .xai import grad_cam, lrp, shap_explanation, overlay_heatmap

logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get("MODEL_PATH", "model_weights.pt")
DEMO_DATA_DIR = os.environ.get("DEMO_DATA_DIR", "demo_data")

app = FastAPI(title="Brain Tumour XAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — restrict this for real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = BrainTumorCNN(in_channels=1, input_size=IMG_SIZE).to(device)
model_loaded = False
background_cache = None
_inference_lock = threading.Lock()


def _load_model():
    global model_loaded
    if os.path.isfile(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.eval()
        model_loaded = True
    else:
        model_loaded = False


def _load_background(n=16):
    """Small background sample set for SHAP's GradientExplainer, drawn from demo_data."""
    global background_cache
    if background_cache is not None:
        return background_cache
    if not os.path.isdir(DEMO_DATA_DIR):
        return None
    paths = []
    # accept both the synthetic layout (tumor/notumor, from train_demo.py)
    # and the Kaggle brain-tumor dataset layout (yes/no) shipped in demo_data
    for cls in ("tumor", "yes", "notumor", "no"):
        cls_dir = os.path.join(DEMO_DATA_DIR, cls)
        if os.path.isdir(cls_dir):
            paths += [os.path.join(cls_dir, f) for f in os.listdir(cls_dir)[: n // 2]]
    tensors = []
    for p in paths[:n]:
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        # demo images vary in size; match the /predict preprocessing (128x128)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE)).astype(np.float32) / 255.0
        img = (img - 0.5) / 0.5
        tensors.append(torch.from_numpy(img).unsqueeze(0))
    if not tensors:
        return None
    background_cache = torch.stack(tensors)
    return background_cache


_load_model()


def _preprocess(image_bytes: bytes) -> tuple[torch.Tensor, np.ndarray]:
    """Returns (model_input_tensor[1,1,H,W], display_uint8[H,W])."""
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("L")
    pil_img = pil_img.resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(pil_img).astype(np.float32) / 255.0
    display_img = np.uint8(arr * 255)
    norm = (arr - 0.5) / 0.5
    tensor = torch.from_numpy(norm).unsqueeze(0).unsqueeze(0).float()
    return tensor, display_img


def _encode_png(bgr_uint8: np.ndarray) -> str:
    success, buf = cv2.imencode(".png", bgr_uint8)
    if not success:
        raise RuntimeError("PNG encoding failed")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_loaded, "device": str(device)}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="No trained model found. Run train_demo.py (or train_real.py after "
                   "downloading BraTS) to produce model_weights.pt first.",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: .png, .jpg, .jpeg.",
        )

    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file is too large. Maximum size is {MAX_UPLOAD_MB} MB.",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file is too large. Maximum size is {MAX_UPLOAD_MB} MB.",
        )
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    with _inference_lock:
        try:
            input_tensor, display_img = _preprocess(contents)
        except Exception:
            logger.exception("Failed to preprocess uploaded image")
            raise HTTPException(status_code=400, detail="Invalid or unreadable image file.")

        with torch.no_grad():
            logit = model(input_tensor.to(device))
            prob = torch.sigmoid(logit).item()

        label = "Tumour Detected" if prob >= 0.5 else "No Tumour Detected"
        confidence = prob if prob >= 0.5 else 1 - prob

        # ---- Grad-CAM ----
        cam = grad_cam(model, input_tensor.clone(), device)
        cam_overlay = overlay_heatmap(display_img, cam, cv2.COLORMAP_JET)

        # ---- LRP ----
        lrp_map = lrp(model, input_tensor.clone(), device)
        lrp_overlay = overlay_heatmap(display_img, lrp_map, cv2.COLORMAP_INFERNO)

        # ---- SHAP ----
        background = _load_background()
        if background is not None:
            shap_mag, _ = shap_explanation(model, input_tensor.clone(), device, background, n_samples=40)
            shap_overlay = overlay_heatmap(display_img, shap_mag, cv2.COLORMAP_VIRIDIS)
            shap_b64 = _encode_png(shap_overlay)
        else:
            shap_b64 = None

        original_b64 = _encode_png(cv2.cvtColor(display_img, cv2.COLOR_GRAY2BGR))

        return JSONResponse(
            {
                "prediction": label,
                "raw_probability": round(prob, 6),
                "confidence": round(confidence * 100, 2),
                "original_image": original_b64,
                "gradcam": _encode_png(cam_overlay),
                "lrp": _encode_png(lrp_overlay),
                "shap": shap_b64,
            }
        )
