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
- **FastAPI Backend Services**: High-performance RESTful API serving predictions, raw confidence metrics, and base64-encoded image heatmaps.
- **Modern Diagnostic Console**: Reactive frontend built with React 19 and Vite, offering dynamic slice uploads, real-time metrics, and synchronized multi-heatmap visual comparisons.
- **BraTS 2021 & Synthetic Pipeline**: Built-in data processing tools (`prepare_brats.py` and `train_real.py`) for processing 3D `.nii.gz` volumes alongside a synthetic demo mode for instant evaluation.

---

## 📁 Project Structure

```
NeuroScan-XAI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI endpoints (/health, /predict) & middleware
│   │   ├── model.py         # BrainTumorCNN model definition & layer mappings
│   │   └── xai.py           # Unified Grad-CAM, LRP, and SHAP heatmaps
│   ├── tests/               # Pytest regression suite (13 tests)
│   ├── demo_data/           # Kaggle brain MRI slices (yes/ = tumour, no/ = normal); original copy in brain_tumor_dataset/
│   ├── model_weights.pt     # Pre-trained CNN model weights
│   ├── prepare_brats.py     # 3D BraTS NIfTI (.nii.gz) -> 2D PNG slice converter
│   ├── train_demo.py        # Demo dataset generator and trainer
│   ├── train_real.py        # Stratified training pipeline with data augmentation
│   └── requirements.txt     # Python dependencies with minimum version bounds
└── frontend/
    ├── src/
    │   ├── App.jsx          # Interactive diagnostic console component
    │   ├── App.css          # Dark-mode medical UI design system
    │   └── main.jsx         # Vite entry point
    ├── index.html           # HTML template
    └── package.json         # React & Vite dependencies
```

> **Data assets note:** `backend/demo_data/` contains the Kaggle brain MRI dataset twice — as `no/` (98 images) and `yes/` (155 images), and byte-identical copies under `brain_tumor_dataset/no/` and `brain_tumor_dataset/yes/` (the "original dataset" copy added in commit `4d0f5ed`). The duplicate (~8.9 MB) is retained intentionally; removing it is deferred to the repository owner. The backend reads only `no/` and `yes/` (or synthetic `tumor/`/`notumor/` slices that `train_demo.py` generates when `demo_data/` is absent) — the duplicate folder is never read at runtime.

---

## 💻 Tech Stack

- **Deep Learning & XAI**: PyTorch, Captum, SHAP, OpenCV, NumPy, Scikit-Learn, NiBabel
- **Backend API**: FastAPI, Uvicorn, Python-Multipart, Pillow
- **Frontend App**: React 19, Vite, Vanilla CSS

---

## 🚀 Quick Start

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
