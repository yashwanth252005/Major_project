"""
FastAPI backend for the Brain Tumour Detection + Unified XAI dashboard.

Endpoints:
  GET  /health               -> liveness check + model status
  POST /predict              -> upload an MRI slice (png/jpg), get back
                                 { prediction, confidence, gradcam, lrp, shap }
                                 where the three XAI fields are base64 PNG
                                 heatmap overlays. The scan is persisted to
                                 the history DB and the stored record (id,
                                 metadata) is merged into the response.
  GET  /history              -> scan history (metadata only, no images)
  GET  /history/{scan_id}    -> one full scan record incl. XAI images
  DELETE /history/{scan_id}  -> delete one scan record
"""

import base64
import logging
import os
import threading
import time

import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db as app_db
from .config import IMG_SIZE, MAX_UPLOAD_BYTES, ALLOWED_IMAGE_EXTENSIONS, MAX_UPLOAD_MB
from .model import BrainTumorCNN
from .model_info import model_fingerprint
from .preprocessing import image_dimensions, preprocess_bytes as _preprocess
from .xai import grad_cam, lrp, shap_explanation, overlay_heatmap

logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get("MODEL_PATH", "model_weights.pt")
DEMO_DATA_DIR = os.environ.get("DEMO_DATA_DIR", "demo_data")
MODEL_NAME = "BrainTumorCNN"

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

    t0 = time.perf_counter()
    with _inference_lock:
        try:
            src_w, src_h = image_dimensions(contents)
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

        payload = {
            "prediction": label,
            "raw_probability": round(prob, 6),
            "confidence": round(confidence * 100, 2),
            "original_image": original_b64,
            "gradcam": _encode_png(cam_overlay),
            "lrp": _encode_png(lrp_overlay),
            "shap": shap_b64,
        }
        processing_time_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Persist outside the inference lock so history I/O never blocks other scans.
    try:
        rec = app_db.insert_scan(
            {
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(contents),
                "source_width": src_w,
                "source_height": src_h,
                "prediction": payload["prediction"],
                "confidence": payload["confidence"],
                "raw_probability": payload["raw_probability"],
                "processing_time_ms": processing_time_ms,
                "model_name": MODEL_NAME,
                "model_fingerprint": model_fingerprint(MODEL_PATH),
                "original_image": payload["original_image"],
                "gradcam": payload["gradcam"],
                "lrp": payload["lrp"],
                "shap": payload["shap"],
            }
        )
    except Exception:
        logger.exception("Failed to persist scan history")
    else:
        payload["id"] = rec["id"]
        payload["created_at"] = rec["created_at"]
        payload["filename"] = rec["filename"]
        payload["content_type"] = rec["content_type"]
        payload["size_bytes"] = rec["size_bytes"]
        payload["source_dimensions"] = {
            "width": rec["source_width"],
            "height": rec["source_height"],
        }
        payload["processing_time_ms"] = rec["processing_time_ms"]
        payload["model_name"] = rec["model_name"]
        payload["model_fingerprint"] = rec["model_fingerprint"]

    return JSONResponse(payload)


@app.get("/history")
def history_list():
    """Scan history — metadata only (no base64 image payloads)."""
    try:
        rows = app_db.list_scans()
    except Exception:
        logger.exception("History storage error")
        raise HTTPException(status_code=500, detail="History storage error.")
    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "filename": row["filename"],
                "content_type": row["content_type"],
                "size_bytes": row["size_bytes"],
                "source_dimensions": {
                    "width": row["source_width"],
                    "height": row["source_height"],
                },
                "prediction": row["prediction"],
                "confidence": row["confidence"],
                "raw_probability": row["raw_probability"],
                "processing_time_ms": row["processing_time_ms"],
                "model_name": row["model_name"],
            }
        )
    return items


@app.get("/history/{scan_id}")
def history_detail(scan_id: str):
    try:
        rec = app_db.get_scan(scan_id)
    except Exception:
        logger.exception("History storage error")
        raise HTTPException(status_code=500, detail="History storage error.")
    if rec is None:
        raise HTTPException(status_code=404, detail="Scan record not found.")
    return rec


@app.delete("/history/{scan_id}")
def history_delete(scan_id: str):
    try:
        deleted = app_db.delete_scan(scan_id)
    except Exception:
        logger.exception("History storage error")
        raise HTTPException(status_code=500, detail="History storage error.")
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan record not found.")
    return Response(status_code=204)
