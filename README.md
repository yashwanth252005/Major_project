# NeuroScan XAI — Brain Tumour Detection with Explainable AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-ee4c2c.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0+-61dafb.svg)](https://react.dev/)

**NeuroScan XAI** is a deep learning and Explainable AI (XAI) platform designed for binary brain tumor classification (Tumor / Non-Tumor) on FLAIR MRI slices. The framework integrates a custom Convolutional Neural Network (CNN) with a multi-method interpretability suite—combining region-level, pixel-level, and feature-level explanations into a unified diagnostic dashboard.

---

## ⚡ Technical Highlights

- **Custom CNN Architecture**: A lightweight 4-block convolutional network (`Conv2d` -> `ReLU` -> `MaxPool2d`) optimized for rapid inference and interpretable feature extraction without transfer learning dependencies.
- **Unified XAI Attribution Suite**:
  - **Grad-CAM**: Highlights regional attention maps from the final convolutional layer.
  - **LRP (Layer-wise Relevance Propagation)**: Computes pixel-wise relevance scores to reveal exact input feature attributions.
  - **SHAP (SHapley Additive exPlanations)**: Employs `GradientExplainer` with background baseline sampling for feature contribution mapping.
- **FastAPI Backend Services**: High-performance RESTful API serving predictions, raw confidence metrics, and base64-encoded image heatmaps, plus persisted scan history (SQLite), aggregate stats, model transparency endpoints (`/model-info`, `/ready`), and sanitized error handling on every route.
- **Modern Diagnostic Console**: React 19 + Vite single-page app (HashRouter) covering upload/analyze, a history explorer, a per-scan metadata report with multipage PDF export, and an insights dashboard built on the history statistics.
- **Evaluation & Reliability Framework**: `backend/evaluation/` CLI producing metrics, confusion-matrix, calibration and reliability artifacts; the official evaluation run is committed under `docs/evaluation/`.
- **BraTS 2021 & Synthetic Pipeline**: Built-in data processing tools (`prepare_brats.py` and `train_real.py`) for processing 3D `.nii.gz` volumes alongside a synthetic demo mode for instant evaluation.

---

## 📁 Project Structure

```
NeuroScan-XAI/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI: backend pytest + frontend build/lint on push/PR
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI endpoints, middleware, model loading
│   │   ├── model.py            # BrainTumorCNN model definition & layer mappings
│   │   ├── xai.py              # Unified Grad-CAM, LRP, and SHAP heatmaps
│   │   ├── config.py           # Image size, upload limits, allowed extensions
│   │   ├── db.py               # SQLite scan-history persistence (neuroscan.db)
│   │   ├── model_info.py       # /model-info + /ready metadata, weights fingerprint
│   │   └── preprocessing.py    # Image decode/resize/normalize for inference
│   ├── evaluation/             # Evaluation framework & CLI (metrics, calibration, plots)
│   ├── tests/                  # Pytest regression suite (71 tests)
│   ├── pytest.ini              # Pytest config (testpaths, markers)
│   ├── requirements.txt        # Runtime Python dependencies with minimum version bounds
│   ├── requirements-dev.txt    # Dev/test-only Python dependencies
│   ├── demo_data/              # Kaggle brain MRI slices (yes/ = tumour, no/ = normal)
│   ├── model_weights.pt        # Pre-trained CNN model weights
│   ├── prepare_brats.py        # 3D BraTS NIfTI (.nii.gz) -> 2D PNG slice converter
│   ├── train_demo.py           # Demo dataset generator and trainer
│   └── train_real.py           # Stratified training pipeline with data augmentation
├── docs/
│   └── evaluation/             # Official evaluation snapshot (EVAL-001)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # HashRouter SPA shell: nav, health/model readouts
│   │   ├── api.js              # Backend API client (fetch helpers)
│   │   ├── xaiMethods.js       # XAI method registry for the UI
│   │   ├── exportPdf.js        # Multipage PDF report export (jsPDF + html2canvas)
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Upload/analyze console with XAI overlays
│   │   │   ├── HistoryList.jsx # Scan-history explorer
│   │   │   ├── ScanDetail.jsx  # Per-scan metadata report incl. PDF export
│   │   │   └── Insights.jsx    # Insights dashboard over history statistics
│   │   ├── App.css             # Dark-mode medical UI design system
│   │   ├── index.css           # Base styles
│   │   └── main.jsx            # Vite entry point
│   ├── index.html              # HTML template
│   └── package.json            # React, Vite, jsPDF dependencies
└── LICENSE                     # MIT License
```

> **Data assets note:** `backend/demo_data/` contains the Kaggle brain MRI dataset twice — as `no/` (98 images) and `yes/` (155 images), and byte-identical copies under `brain_tumor_dataset/no/` and `brain_tumor_dataset/yes/` (the "original dataset" copy added in commit `4d0f5ed`). The duplicate (~8.9 MB) is retained intentionally; removing it is deferred to the repository owner. The backend reads only `no/` and `yes/` (or synthetic `tumor/`/`notumor/` slices that `train_demo.py` generates when `demo_data/` is absent) — the duplicate folder is never read at runtime.

---

## 💻 Tech Stack

- **Deep Learning & XAI**: PyTorch, Captum, SHAP, OpenCV, NumPy, Scikit-Learn, NiBabel
- **Backend API**: FastAPI, Uvicorn, Python-Multipart, Pillow
- **Frontend App**: React 19, Vite, Vanilla CSS

---

## 🚀 Quick Start

> **Order matters:** start the **backend first**, then the frontend — the frontend probes the API on load. The first successful `/predict` creates `neuroscan.db` (a gitignored SQLite scan-history store) in the backend working directory.

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment (optional)
python -m venv venv
# On Windows: venv\Scripts\activate | On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be live at `http://localhost:8000`. Test endpoint health at `http://localhost:8000/health`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Open `http://localhost:5173` in your browser. Upload sample MRI slices from `backend/demo_data/yes/` or `backend/demo_data/no/` to view real-time predictions and XAI overlay heatmaps.

---

## 🔌 API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check + model status |
| POST | `/predict` | Analyze an MRI slice: prediction, confidence, Grad-CAM/LRP/SHAP overlays; persists to history |
| GET | `/history` | Scan history (metadata only), newest first |
| GET | `/history/{id}` | Full scan record incl. images |
| DELETE | `/history/{id}` | Remove a scan record |
| GET | `/stats` | Application-history statistics over stored scans |
| GET | `/model-info` | Model metadata + checkpoint fingerprint (no paths, no performance claims) |
| GET | `/ready` | Readiness probe; returns 503 when model assets are unavailable |

---

## 🧪 Running the tests

**Backend** — 71 tests; the suite includes one `slow` real-inference end-to-end test that runs by default:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

**Frontend**:

```bash
cd frontend
npm install
npm run build
npm run lint
```

CI runs the same backend and frontend checks on every push/PR — see `.github/workflows/ci.yml`.

---

## 📈 Model Evaluation

The `backend/evaluation/` package ships a standalone CLI that evaluates the trained model through the exact deployed inference path (same `BrainTumorCNN` loading and preprocessing as the FastAPI app):

```bash
cd backend
python -m evaluation.evaluate --data-dir demo_data --output-dir evaluation_output --threshold 0.5
```

It writes a full artifact set: `metrics.json`, `predictions.csv`, per-class metrics, confusion matrices, calibration data, a reliability diagram, and an auto-generated `EVALUATION_REPORT.md`.

The official evaluation run (**EVAL-001**) is committed under `docs/evaluation/`.

> On the bundled Kaggle evaluation set (253 images), the frozen model reaches accuracy 0.6126 and balanced accuracy 0.6370 — a domain-shifted, non-clinical dataset; these figures are NOT clinically meaningful and the model must not be used for diagnosis. Full metrics, calibration analysis and limitations: docs/evaluation/EVALUATION_REPORT.md.

---

## 📊 BraTS 2021 Dataset Integration

To train the model on full-scale clinical dataset (BraTS 2021 FLAIR volumes):

1. Download dataset subfolders containing `*_flair.nii.gz` and `*_seg.nii.gz` volumes (e.g., from [Kaggle BraTS 2021](https://www.kaggle.com/datasets/dschettler8845/brats-2021-task1)).
2. Set `RAW_DATA_DIR` in `backend/prepare_brats.py` to your raw dataset path.
3. Run preprocessing and training:

```bash
cd backend
python prepare_brats.py   # Extracts & cleans brain tissue slices -> brats_prepared/
python train_real.py      # Trains CNN with data augmentation & saves model_weights.pt
```

Restart `uvicorn` to run inference using your newly trained model weights.

---

## 🔮 Future Work

- **Multi-Class Segmentation**: Extend architecture to segment specific tumor regions (enhancing tumor, edema, necrotic core).
- **3D Spatial Attribution**: Expand XAI techniques from 2D slices to full 3D volumetric MRI scans.
- **Clinical Integration**: DICOM format support and EHR integration capability.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
