"""Shared production preprocessing (used by both the FastAPI app and the evaluator)."""
import io

import numpy as np
import torch
from PIL import Image

from .config import IMG_SIZE


def preprocess_bytes(image_bytes: bytes) -> tuple[torch.Tensor, np.ndarray]:
    """Returns (model_input_tensor[1,1,H,W], display_uint8[H,W])."""
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("L")
    pil_img = pil_img.resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(pil_img).astype(np.float32) / 255.0
    display_img = np.uint8(arr * 255)
    norm = (arr - 0.5) / 0.5
    tensor = torch.from_numpy(norm).unsqueeze(0).unsqueeze(0).float()
    return tensor, display_img
