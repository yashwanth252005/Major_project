"""
Bridge between Django and Ankith/Yashwanth's model code in Brain_Tumor_AI/.

We do NOT modify anything inside Brain_Tumor_AI/. That folder's predict.py
loads config.json / models/best_densenet121.pth / background/* using paths
that are relative to its own directory, so the only thing we need to do
here is:

  1. add Brain_Tumor_AI/ to sys.path so `from utils.model import build_model`
     resolves correctly inside predict.py, and
  2. chdir into Brain_Tumor_AI/ for the one moment the predictor is built
     (which is when it reads config.json / the .pth file / the background
     folder), then chdir back.

The heavy model load (DenseNet121 + SHAP background tensors) only happens
once, the first time a prediction is requested, and is cached for the life
of the process.
"""

import os
import sys
import threading

from django.conf import settings

_predictor = None
_lock = threading.Lock()


def _ensure_on_path():
    brain_dir = str(settings.BRAIN_TUMOR_AI_DIR)
    if brain_dir not in sys.path:
        sys.path.insert(0, brain_dir)


def get_predictor():
    """Lazily build (and cache) the BrainTumorPredictor singleton."""
    global _predictor

    if _predictor is not None:
        return _predictor

    with _lock:
        if _predictor is None:
            _ensure_on_path()

            brain_dir = str(settings.BRAIN_TUMOR_AI_DIR)
            cwd = os.getcwd()
            try:
                os.chdir(brain_dir)
                # Imported lazily so Django can start even if torch/shap
                # aren't installed yet, and so reload doesn't double-import.
                from predict import BrainTumorPredictor  # noqa: PLC0415

                _predictor = BrainTumorPredictor()
            finally:
                os.chdir(cwd)

    return _predictor


def run_prediction(image_path: str) -> dict:
    """
    image_path: absolute path to a temp file on disk (any location - the
    predictor only needs it at prediction time, not at load time).
    """
    predictor = get_predictor()
    return predictor.predict(image_path)
