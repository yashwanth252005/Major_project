# A Unified XAI Framework for Interpreting Deep Learning Models in Brain Tumor Detection

A brain MRI classifier paired with three complementary explainability techniques —
**Grad-CAM**, **Integrated Gradients**, and **SHAP** — served through a Django API and a
React dashboard, so a prediction always comes with a visual explanation instead of a
black-box label.

Built as a Major Project (BCS685, VI Semester, VTU) at Sapthagiri College of Engineering,
Dept. of CSE, 2025–2026.

---

## Team & Contributions

| Contributor | Component | What they built |
|---|---|---|
| **Yashwanth E S** | [`Brain_Tumor_AI/`](./Brain_Tumor_AI) | The CNN (DenseNet121-based) trained on BraTS 2021 FLAIR MRI scans, plus the Grad-CAM, SHAP, and Integrated Gradients explainability pipeline (`predict.py`, `utils/`). |
| **Ankith V Hullamani** | [`backend/`](./backend) & [`frontend/`](./frontend) | Django REST API wrapping the model, scan-history persistence, and the React/Tailwind dashboard (upload → prediction → XAI visualizations → PDF report). |
| Aaryan Kumar, Tejaswini K | Research & documentation | Literature survey, comparative analysis, and project report. |
| Dr. Kamalakshi Naganna | Guide | Professor & Head, Dept. of CSE — project supervision. |

`Brain_Tumor_AI/` is treated as a contribution boundary: the backend imports and calls
that code but never modifies it (see [Architecture](#architecture) below).

---

## What this project does

Deep CNNs are effective at spotting tumors in MRI scans but give no reasoning for their
predictions — a problem in a clinical setting where a doctor needs to know *why* the model
flagged a scan before trusting it. This project addresses that by:

1. Classifying an uploaded FLAIR MRI slice with a CNN (tumor / non-tumor).
2. Explaining that prediction from three different angles at once:
   - **Grad-CAM** — region-level heatmap ("where" the network looked)
   - **Integrated Gradients** — pixel-level attribution ("which pixels exactly")
   - **SHAP** — feature-level contribution ("what pushed the decision either way")
3. Presenting all three side by side in a web dashboard, saving every scan to a
   history log, and exporting any scan as a PDF report.

> **Note on XAI methods:** the original literature survey (see `Brain_Tumor_AI`'s research
> paper) references Grad-CAM, **LRP**, and SHAP. The implemented pipeline actually ships
> Grad-CAM, **Integrated Gradients**, and SHAP — Integrated Gradients serves the same
> "fine-grained pixel attribution" role LRP would, but LRP itself was not implemented in
> this phase.

---

## Architecture

```
Major_project/
├── Brain_Tumor_AI/        ← Yashwanth's model (untouched by backend/frontend work)
│   ├── predict.py           BrainTumorPredictor class - the single entry point
│   ├── config.json           class labels, thresholds, etc.
│   ├── models/
│   │   └── best_densenet121.pth
│   ├── background/           reference images used to build the SHAP explainer
│   └── utils/                 model loading, preprocessing, Grad-CAM/SHAP/IG code
│
├── backend/                ← Django REST API (Ankith)
│   ├── core/                  settings, urls
│   ├── api/
│   │   ├── inference.py        loads Brain_Tumor_AI's predictor once, caches it
│   │   ├── models.py            Scan (persisted prediction + XAI images)
│   │   ├── views.py              /predict, /history endpoints
│   │   └── serializers.py
│   └── requirements.txt
│
└── frontend/                ← React + Vite + Tailwind dashboard (Ankith)
    └── src/
        ├── pages/               Dashboard, History, ScanDetail
        ├── components/          UploadCard, ResultPanel, ReportImage, Navbar
        └── api/client.js         talks to the Django API
```

**How the backend calls the model without editing it:** `Brain_Tumor_AI/predict.py`
loads `config.json`, the `.pth` weights, and the SHAP `background/` set using paths
relative to its own folder. `backend/api/inference.py` temporarily changes into
`Brain_Tumor_AI/` only for that one-time model load, then serves every request after
that from the cached instance — his code is imported as-is, never modified.

**Request flow:**
```
Browser (React) → POST /api/predict/ (multipart image)
                → Django view → Brain_Tumor_AI.predict.BrainTumorPredictor.predict()
                → result saved as a Scan row (SQLite) + returned as JSON
                → React renders prediction + Grad-CAM/SHAP/IG images
                → optional: view full report at /history/:id → Export PDF
```

---

## Tech stack

| Layer | Tools |
|---|---|
| Model | PyTorch, torchvision, DenseNet121, `grad-cam`, `shap`, `captum` (Integrated Gradients), OpenCV, Matplotlib |
| Backend | Django 4.2, Django REST Framework, django-cors-headers, SQLite |
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios, jsPDF + html2canvas (PDF export) |

---

## Features

- Drag-and-drop MRI upload with live preview
- Tumor / non-tumor prediction with confidence score and processing time
- Three-way explainability view (Grad-CAM, Integrated Gradients, SHAP) per prediction
- Automatic scan history (every prediction persisted with its images)
- Per-scan detail page with one-click PDF export of the full report
- CORS-enabled dev setup so frontend and backend run independently

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Git
- (Optional but recommended) an NVIDIA GPU with CUDA for faster inference — the model
  falls back to CPU automatically if none is found

### 1. Clone the repository

```bash
git clone https://github.com/yashwanth252005/Major_project.git
cd Major_project
```

Make sure the folder layout matches the diagram above — `Brain_Tumor_AI/`, `backend/`,
and `frontend/` should all be siblings at the repo root.

### 2. Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt   # installs Django + the model's ML dependencies
python manage.py migrate          # creates db.sqlite3 (auth tables + Scan table)
python manage.py runserver        # http://127.0.0.1:8000
```

Sanity check: `curl http://127.0.0.1:8000/api/health/` → `{"status": "ok"}`

The first `/api/predict/` call is slower than the rest — it's the one-time cost of
loading DenseNet121's weights and building the SHAP background explainer. Every call
after that reuses the cached model.

### 3. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

The dev server proxies `/api/*` requests to `http://127.0.0.1:8000`, so no extra CORS
configuration is needed as long as both servers are running.

### 4. Use it

Open `http://localhost:5173`, upload a FLAIR MRI image (`.jpg`, `.jpeg`, `.png`, or
`.bmp`), and click **Analyze Scan**. Check `/history` afterward to see it saved, and
open any entry to export it as a PDF.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health/` | Liveness check |
| `POST` | `/api/predict/` | Body: `multipart/form-data`, field `image`. Runs the model, saves the result, returns prediction + all three XAI images (base64 PNG) |
| `GET` | `/api/history/` | List all saved scans (lightweight: no XAI images, just thumbnail + prediction) |
| `GET` | `/api/history/<uuid>/` | Full detail for one scan, including all XAI images |
| `DELETE` | `/api/history/<uuid>/` | Delete a saved scan |

---

## Known Limitations

- Binary classification only (tumor / non-tumor) — no tumor sub-type (glioma,
  meningioma, pituitary) classification yet.
- LRP is described in the research literature but not implemented; Integrated Gradients
  is used in its place.
- SHAP computation is the slowest of the three explainers and is not optimized for
  real-time use.
- Scan images are stored as base64 text in SQLite for simplicity — fine for a project
  demo, but would need to move to file/object storage for production scale.

## Future Work (Phase II)

- Multi-class tumor type classification (glioma / meningioma / pituitary / no tumor)
- Tumor segmentation (exact boundaries, not just presence)
- Support for multiple MRI modalities (T1, T2, T1ce, FLAIR) together
- A real LRP explainer alongside Grad-CAM/SHAP/Integrated Gradients
- Clinical validation with radiologists

---

## Academic Context

Submitted in partial fulfillment of **Major Project Phase I (BCS685) — VI Semester**,
Bachelor of Engineering in Computer Science & Engineering, Visvesvaraya Technological
University, Belagavi, under the guidance of **Dr. Kamalakshi Naganna**, Professor & Head,
Dept. of CSE, Sapthagiri College of Engineering.

The accompanying literature survey was published in *International Journal for Research
in Applied Science & Engineering Technology (IJRASET)*, Volume 14, Issue V, May 2026,
DOI: [10.22214/ijraset.2026.82087](https://doi.org/10.22214/ijraset.2026.82087).
