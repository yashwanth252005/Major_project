# Project Execution Ledger

> Persistent continuity record for phased implementation of **NeuroScan-XAI** (local repository `NeuroScan-XAI-main`, a.k.a. the Major Project "A Unified XAI Framework for Interpreting Deep Learning Models in Brain Tumor Detection").
>
> Read together with `MAJOR_PROJECT_FEATURE_IMPLEMENTATION_HANDOFF.md`.
>
> Never delete previous entries. Append corrections instead of silently rewriting historical records.
>
> **Repository-first rule:** This ledger is not the source of truth for the current implementation. The checked-out repository is. Every new session must re-verify material facts directly from code/config/migrations/tests before relying on a ledger entry.
>
> Source-of-truth order for current-state facts:
>
> `checked-out repository → Git history → executable evidence → repo-consistent docs → this ledger → handoff → chat memory`
>
> The ledger records execution history and approvals. It must never override the repository.


---

## Repository-as-Source-of-Truth Control

The repository is authoritative for all factual claims about the current system.

This ledger may contain stale information after later commits. Therefore every session must verify material facts against the checked-out repository before acting.

Use the following distinction:

```text
Repository = current implementation truth
Handoff    = intended future change contract
Ledger     = historical execution/audit record
```

If this ledger conflicts with the repository:

1. inspect the actual code/config/migrations/tests,
2. treat the repository as authoritative,
3. append a correction entry to this ledger,
4. do not rewrite historical entries silently,
5. update the next phase plan if necessary.

A ledger entry is never sufficient evidence that:

- an endpoint exists,
- a response field exists,
- a migration applied,
- a test passed,
- the model hash is unchanged,
- evaluation results are valid.

Those require current repository/executable verification.


---

## Repository Identity

**Repository:** NeuroScan-XAI (local checkout; origin remote as configured, not pushed during this work)  
**Working branch:** `main`  
**Baseline commit (bootstrap):** `4d0f5ed03c6a92b672608db4ba41fe71c7b1ed99` ("Added original datasets")  
**Baseline date:** 2026-09-25  
**Verified by:** direct inspection of `backend/app/*`, `frontend/src/*`, `git log`, executable smoke test (2026-09-25).

---

## Frozen Compatibility Contract

**Corrected per CORRECTION C-001 (2026-09-25).** The original template contract described a
Django/DRF + DenseNet121 four-class system that has never existed in this checkout. The
authoritative frozen contract, derived from the checked-out repository, is:

The following must remain intact unless a phase explicitly authorizes an additive change:

- React 19 + Vite frontend (`frontend/`, single-page `App.jsx` console)
- **FastAPI** backend (`backend/app/main.py`, served via uvicorn)
- PyTorch **BrainTumorCNN** (custom 4-block CNN, `backend/app/model.py`)
- existing trained checkpoint: `backend/model_weights.pt`
- binary classification semantics: `Tumour Detected` / `No Tumour Detected` (sigmoid logit, 0.5 threshold)
- preprocessing: grayscale, resize 128×128, `/255.0`, normalize `(x-0.5)/0.5`
- XAI methods: **Grad-CAM**, **LRP** (manual epsilon-LRP), **SHAP** (GradientExplainer)
- existing API endpoints and fields:
  - `GET /health` → `{status, model_loaded, device}`
  - `POST /predict` → `{prediction, raw_probability, confidence, original_image, gradcam, lrp, shap}`
- upload → prediction → XAI workflow
- model checkpoint byte-for-byte unchanged (SHA-256 `5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1`)

Intended additive end-state (from the handoff, adapted to this stack): SQLite-backed scan history,
history explorer, insights, enhanced report + client-side PDF export, `/api/model-info` and
readiness endpoints, standalone evaluation framework. No framework replacement (no Django/Flask
introduction, no new frontend framework), no retraining, no replacement of the three XAI methods.

---

## Authoritative Phase Order

```text
Phase 0 — Baseline and regression safety
Phase 1 — Documentation/hygiene fixes
Phase 2 — Input and inference robustness
Phase 3A — Evaluation framework
Phase 3B — Independent dataset evaluation when dataset is available
Phase 4 — Scan metadata/report/PDF
Phase 5 — History Explorer/Insights
Phase 6 — Model information/readiness/transparency
Phase 7 — Final testing/CI/documentation
```

Dependency rule:

```text
0 -> 1 -> 2 -> 3A -> 4 -> 5 -> 6 -> 7
```

Phase 3B may run after Phase 3A whenever an approved labeled independent dataset becomes available.

Performance claims are forbidden while:

```text
Evaluation Results = PENDING DATASET
```

---

## Baseline Snapshot

### Git

```text
Branch: main
HEAD: 4d0f5ed03c6a92b672608db4ba41fe71c7b1ed99
Working tree at bootstrap: modified backend/app/main.py (pre-existing robustness fix, committed
separately before Phase 0 — see CORRECTION C-001 notes); untracked control documents
AGENT_EXECUTION_PROMPT.md, MAJOR_PROJECT_FEATURE_IMPLEMENTATION_HANDOFF.md,
PROJECT_EXECUTION_LEDGER.md
```

### Model

```text
Path: backend/model_weights.pt
SHA-256: 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1
Size: 4,589,291 bytes
Provenance: commit e09d305 "Replace synthetic model with BraTS 2021 trained model";
trained via backend/train_real.py on prepared BraTS 2021 FLAIR slices (brats_prepared/,
not present in repo)
```

### Model Configuration

```text
model_name: BrainTumorCNN (custom 4-block CNN: Conv-ReLU-MaxPool x4, FC head, single logit)
image_size: 128 (IMG_SIZE in backend/app/main.py, model.py default, train scripts)
num_classes: 1 (single sigmoid logit -> binary)
class_names: "Tumour Detected" (prob >= 0.5) / "No Tumour Detected" (prob < 0.5)
normalization: arr/255.0 then (arr - 0.5) / 0.5  (i.e. mean=0.5, std=0.5, grayscale)
channels: 1 (grayscale, .convert("L"))
```

### Existing Backend Routes

```text
GET  /health   -> {status: "ok", model_loaded: bool, device: str}
POST /predict  -> multipart file -> {prediction, raw_probability, confidence,
                   original_image, gradcam, lrp, shap} (base64 PNGs; shap null if
                   no background data available)
503 when model weights missing; 400 when image unreadable
```

### Existing Frontend Routes

```text
Single-page app (no router): / only — upload -> preview -> predict -> XAI dashboard
API base: import.meta.env.VITE_API_BASE || http://localhost:8000
```

### Baseline Test/Build Status

```text
Backend: NO tests exist (no tests directory anywhere).
Frontend: npm run build passes (vite 8; dist assets ~196 kB JS / 7 kB CSS).
Full inference smoke test (2026-09-25, venv python, TestClient):
  GET /health -> 200 {status: ok, model_loaded: true, device: cpu}
  POST /predict demo_data/yes/Y1.jpg -> 200 "Tumour Detected", confidence 99.86,
       raw_probability 0.998644, all three XAI images present (shap non-null)
  POST /predict demo_data/no/1 no.jpeg -> 200 "No Tumour Detected", confidence 99.28,
       raw_probability 0.00718, all three XAI images present
Environment note: backend/venv (Python 3.10.11, torch 2.13.0+cpu, fastapi 0.141.1).
httpx2 2.13.1 installed into venv on 2026-09-25 to enable starlette TestClient
(required by the Phase 0 test suite; to be captured in a dev-requirements file).
```

### Data Assets

```text
backend/demo_data/no/        98 images (Kaggle brain_tumor_dataset, class "no")
backend/demo_data/yes/      155 images (Kaggle brain_tumor_dataset, class "yes")
backend/demo_data/brain_tumor_dataset/{no,yes}/  exact byte-identical duplicate copy
                             of the above (verified by sampled SHA-256 comparison,
                             2026-09-25) added in commit 4d0f5ed
Note: demo_data is NOT the training set of the current checkpoint (BraTS 2021 via
train_real.py). It is used only as SHAP background sampling at inference time.
```

---

## Phase Status Board

| Phase | Planner | Implementor | Reviewer | Gate | Reviewed Commit |
|---|---|---|---|---|---|
| 0 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 1 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 2 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 3A Evaluation Framework | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 3B Evaluation Results | WAITING FOR 3A | WAITING FOR DATASET | NOT STARTED | PENDING DATASET | — |
| 4 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 5 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 6 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |
| 7 | NOT STARTED | NOT STARTED | NOT STARTED | BLOCKED | — |

Allowed role states:

```text
NOT STARTED
IN PROGRESS
COMPLETE
FAILED
NEEDS REVISION
WAITING FOR DATASET
WAITING FOR 3A
```

Allowed gate states:

```text
BLOCKED
APPROVED
APPROVED WITH NOTES
REJECTED
PENDING DATASET
```

---

## Evaluation State

```text
FRAMEWORK STATUS: NOT STARTED
DATASET STATUS: PENDING
DATASET INDEPENDENCE: NOT VERIFIED
RESULT STATUS: PENDING DATASET
RESULT REVIEW STATUS: NOT STARTED
```

### Approved Dataset Record

Complete only when a real labeled evaluation dataset is accepted.

```text
Dataset name:
Source:
Version/release:
License/use notes:
Local path:
Manifest:
Manifest SHA-256:
Sample count:
Class counts:
Independence evidence:
Known overlap risk:
Approved by:
Approval date:
```

Never store sensitive patient information in this ledger.

---

# Phase 0 — Baseline & Regression Safety

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 1 may start:** NO

---

# Phase 1 — Documentation & Hygiene

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 2 may start:** NO

---

# Phase 2 — Input & Inference Robustness

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 3A may start:** NO

---

# Phase 3A — Evaluation Framework

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Framework Gate

```text
FRAMEWORK STATUS: NOT STARTED
DATASET STATUS: PENDING
RESULT STATUS: PENDING DATASET
```

**Phase 4 may start:** NO

A framework can be approved even when the independent dataset is not yet available.

Required approved state before Phase 4:

```text
FRAMEWORK STATUS: APPROVED
```

---

# Phase 3B — Independent Evaluation Execution

> Conditional. Run when an approved labeled independent dataset is available.

## Dataset Approval Record
_Not available._

## Planner Record
_Not started._

## Implementor / Evaluation Run Record
_Not started._

## Independent Results Reviewer Record
_Not started._

## Results Gate

```text
DATASET STATUS: PENDING
DATASET INDEPENDENCE: NOT VERIFIED
RESULT STATUS: PENDING DATASET
```

No model-performance figures may be represented as final while this gate is pending.

---

# Phase 4 — Scan Metadata, Report & PDF

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 5 may start:** NO

---

# Phase 5 — History Explorer & Insights

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 6 may start:** NO

---

# Phase 6 — Model Info, Readiness & Transparency

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Phase 7 may start:** NO

---

# Phase 7 — Final Testing, CI & Documentation

## Planner Record
_Not started._

## Implementor Record
_Not started._

## Independent Reviewer Record
_Not started._

## Gate Decision

**Decision:** BLOCKED  
**Final sign-off allowed:** NO

---

## Cross-Phase Decisions

Use decision IDs such as `D-001`.

Template:

```markdown
### Decision D-001 — <title>

**Phase introduced:**  
**Decision:**  
**Reason:**  
**Affected files:**  
**Locked for later phases:** YES/NO
```

Items that should become locked decisions once chosen include:

- upload limit
- maximum input dimensions
- original image MIME strategy
- model-fingerprint format
- evaluation manifest format
- exact class alias policy
- specificity aggregation wording
- confidence-band definitions
- calibration/ECE binning procedure if implemented

_No decisions recorded yet._

---

## Corrections

Never silently edit completed historical records.

Template:

```markdown
### CORRECTION C-001

**Affected record:**  
**Incorrect value:**  
**Correct value:**  
**Reason:**  
**Evidence:**  
```

_No corrections recorded yet._

### CORRECTION C-001 — Handoff/ledger describe a different (stale) architecture; repository wins

**Affected record:** Frozen Compatibility Contract (template initialization), Baseline Snapshot, Phase interpretations throughout.  
**Incorrect value:** Handoff, ledger template, and `AGENT_EXECUTION_PROMPT.md` all describe the system as Django + DRF + SQLite with a DenseNet121 checkpoint at `Brain_Tumor_AI/models/best_densenet121.pth`, classes `glioma/meningioma/notumor/pituitary` (224px, ImageNet normalization), XAI = Grad-CAM + Integrated Gradients + SHAP, endpoints `/api/health/`, `/api/predict/`, `/api/history/…`, and an existing Scan history/PDF-export feature set.  
**Correct value:** The checked-out repository (`NeuroScan-XAI-main`, HEAD `4d0f5ed`) is a **FastAPI** backend (`backend/app/main.py`) + React 19/Vite single-page frontend with a **custom binary BrainTumorCNN** (`backend/app/model.py`), checkpoint `backend/model_weights.pt` (SHA-256 `5f191bc8…b7bc1`), classes `Tumour Detected` / `No Tumour Detected` (128×128 grayscale, `(x-0.5)/0.5` normalization), XAI = **Grad-CAM + LRP + SHAP**, endpoints `GET /health` and `POST /predict` only. There is no database, no history feature, no report/PDF export, no tests, and no `/api/...` prefix.  
**Reason:** Repository-first rule. The control documents were written for a different/more advanced lineage of this project (`yashwanth252005/Major_project`) and are stale for this checkout. Per the conflict rule, the repository was not modified to match the documents; instead the plan was adapted.  
**Evidence:** Direct file inspection of `backend/app/main.py`, `backend/app/model.py`, `backend/app/xai.py`, `frontend/src/App.jsx`, `frontend/package.json`, `git log`/`git show` (commits `be19683`, `e09d305`, `4d0f5ed`), and an executable smoke test recorded in the Baseline Snapshot (2026-09-25).

**Adaptation consequences for the roadmap (locked for later phases):**
- "Enhance history" features (History Explorer, Insights, Enhanced Report/PDF) have no existing substrate here; they are treated as **additive new features** built on the frozen FastAPI/React stack, with SQLite as the sanctioned persistence layer per the handoff end-state.
- "Existing endpoints that must remain" means `GET /health` and `POST /predict` with exactly the fields listed in the Frozen Compatibility Contract; the `/api/...` path spellings from the handoff do not apply (existing unprefixed paths preserved; new endpoints follow the existing unprefixed convention, e.g. `/stats`, `/model-info`, `/ready`).
- Phase 3 metrics are **binary** (accuracy, precision, recall/sensitivity, specificity, F1, confusion matrix, confidence analysis) — the four-class per-class metric requirements from the handoff do not apply.
- Phase 3B has a viable in-repo dataset: `backend/demo_data` (Kaggle brain MRI, 98 no / 155 yes) was **not** used to train the current BraTS-trained checkpoint; independence is recorded with the caveat that 16 of these images are sampled as SHAP background at inference (no weight updates ever involved). Final dataset approval still happens at Phase 3B.
- Handoff gap list items that do not exist here are recorded as not applicable (e.g. `Brain_Tumor_AI/requirements.txt` shell syntax — this repo's `backend/requirements.txt` is already valid; `.history/` tracking — not present, though the ignore entry is still added cheaply; "AI Summary" label / "securely stored" copy — no such text exists in `App.jsx`).

---

## Interrupted Session Records

Template:

```markdown
### Interrupted Session — Phase N — <Role>

**Current commit:**  
**Working tree:**  
**Completed:**  
**Not completed:**  
**Modified files:**  
**Last successful command:**  
**Current blocker:**  
**Next safe action:**  
```

_None._

---

## Planner Record Template

```markdown
### Planner Record — Phase N

**Session ID:** PHASE-N-PLANNER
**Date:**
**Starting commit:**
**Branch:**
**Model SHA-256:**

#### Repository state inspected
- ...

#### Files inspected
- ...

#### Current behavior confirmed
- ...

#### Planned files to change
- ...

#### Files explicitly frozen
- ...

#### API impact
- ...

#### Migration impact
- ...

#### Risks
- ...

#### Test plan
- ...

#### Acceptance criteria
- ...

#### Planner decision
READY FOR IMPLEMENTATION | BLOCKED

#### Exact next-session instruction
- ...
```

---

## Implementor Record Template

```markdown
### Implementor Record — Phase N

**Session ID:** PHASE-N-IMPLEMENTOR
**Starting commit:**
**Ending commit:**
**Branch:**

#### Planner record followed
- yes/no

#### Files changed
- ...

#### Functional changes
- ...

#### Tests added
- ...

#### Commands executed
```text
...
```

#### Test results
```text
...
```

#### Frontend build result
```text
...
```

#### Migration result
```text
...
```

#### Model SHA-256 after implementation
- ...

#### Deviations from plan
- none / ...

#### Unresolved items
- ...

#### Implementor status
READY FOR REVIEW | BLOCKED

#### Exact reviewer instruction
- ...
```

---

## Independent Reviewer Record Template

```markdown
### Independent Reviewer Record — Phase N

**Session ID:** PHASE-N-REVIEWER
**Reviewed commit:**
**Expected baseline commit:**

#### Diff independently inspected
- ...

#### Architecture integrity
- PASS/FAIL
- notes

#### API compatibility
- PASS/FAIL
- notes

#### Database/migration safety
- PASS/FAIL
- notes

#### Model integrity
- PASS/FAIL
- baseline hash
- current hash

#### Automated tests rerun
```text
...
```

#### Frontend build rerun
```text
...
```

#### Manual regression performed
- ...

#### Blocking findings
- none / ...

#### Non-blocking findings
- none / ...

#### Decision
APPROVED | APPROVED WITH NON-BLOCKING NOTES | REJECTED

#### Required next action
- ...
```

---

## Phase 3 Evaluation Run Record Template

Use for each real evaluation execution.

```markdown
### Evaluation Run EVAL-<ID>

**Date:**
**Git commit:**
**Model SHA-256:**
**Dataset:**
**Dataset manifest SHA-256:**
**Sample count:**
**Class counts:**
**Device:**
**Output directory:**

#### Commands
```text
...
```

#### Required artifacts
- [ ] run_metadata.json
- [ ] predictions.csv
- [ ] metrics.json
- [ ] per_class_metrics.csv
- [ ] confusion_matrix.json
- [ ] confusion_matrix_counts.png
- [ ] confusion_matrix_normalized.png
- [ ] confidence_analysis.csv
- [ ] misclassified_cases.csv
- [ ] EVALUATION_REPORT.md

#### Mandatory metrics
```text
accuracy:
macro precision:
macro recall:
macro F1:
macro specificity:
weighted precision:
weighted recall:
weighted F1:
```

#### Per-class metrics
```text
glioma:
meningioma:
notumor:
pituitary:
```

#### Reliability outputs
```text
correct mean confidence:
incorrect mean confidence:
high-confidence error count:
ECE (if enabled):
Brier score (if enabled):
```

#### Limitations
- ...

#### Independent results review
PENDING | APPROVED | REJECTED
```

---

## Deferred Items

Deliberately excluded from this implementation package:

- authentication
- role-based access control
- PostgreSQL
- object storage
- DICOM
- tumor segmentation
- multimodal MRI
- LRP
- model retraining
- clinical validation
- distributed inference

---

## Known Risks

_Add as discovered._

---

## Open Blockers

_None at initialization._

---

## Final Integrity Record

Complete only after Phase 7 review.

```text
Baseline model SHA-256:
Final model SHA-256:
Hashes match:

Original API endpoints preserved:
Original response fields preserved:
Old Scan records readable:

Phase 3A evaluation framework:
Phase 3B dataset:
Phase 3B result status:

Backend tests:
Frontend build:
Manual regression:
```

If Phase 3B remains pending because no approved dataset was available, final documentation must explicitly state:

```text
Evaluation framework implemented; final independent model-performance
results remain pending an approved labeled evaluation dataset.
```

---

## Final Sign-Off

**Status:** NOT READY

The final reviewer completes this only after all mandatory phase gates are approved.

Phase 3B may remain `PENDING DATASET` only if no final numerical model-performance claim is made.
