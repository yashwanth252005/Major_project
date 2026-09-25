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
| 0 | COMPLETE | COMPLETE | COMPLETE | APPROVED WITH NON-BLOCKING NOTES | 628cd7c (files committed after) |
| 1 | COMPLETE | COMPLETE | COMPLETE | APPROVED WITH NON-BLOCKING NOTES | 2996163 (files committed after) |
| 2 | COMPLETE | COMPLETE | COMPLETE | APPROVED | 1f72ab7 (files committed after) |
| 3A Evaluation Framework | COMPLETE | COMPLETE | COMPLETE | APPROVED | dbf4aea (files committed after) |
| 3B Evaluation Results | COMPLETE | COMPLETE (EVAL-001) | COMPLETE | APPROVED WITH NON-BLOCKING NOTES | 58de4ed (docs committed after) |
| 4 | COMPLETE | COMPLETE (+fix-loop) | COMPLETE | APPROVED WITH NON-BLOCKING NOTES | adbc019 (files committed after) |
| 5 | COMPLETE | COMPLETE | COMPLETE | APPROVED | b13dd4c (files committed after) |
| 6 | COMPLETE | COMPLETE | COMPLETE | APPROVED | 2a75656 (files committed after) |
| 7 | COMPLETE | COMPLETE | COMPLETE | APPROVED WITH NON-BLOCKING NOTES | 435342f (files committed after) |

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
FRAMEWORK STATUS: APPROVED (Phase 3A, 2026-09-25)
DATASET STATUS: APPROVED (2026-09-25, with disclosures — see Phase 3B Dataset Approval Record)
DATASET INDEPENDENCE: VERIFIED (checkpoint predates dataset commit; training external to demo_data; SHAP-background reuse disclosed)
RESULT STATUS: GENERATED AND REVIEWED (EVAL-001 approved with non-blocking notes, 2026-09-25)
RESULT REVIEW STATUS: APPROVED
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

### Planner Record — Phase 0

**Session ID:** PHASE-0-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 628cd7c (post-bootstrap: 18a80d1 docs + 628cd7c pre-existing SHAP-background fix)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (verified unchanged)

#### Repository state inspected
- Clean tree at 628cd7c; no tests anywhere; pytest not installed in backend/venv (Python 3.10.11, torch 2.13.0+cpu, fastapi 0.141.1, starlette 1.6.0, httpx2 2.13.1 present so TestClient works).
- Planner re-verified by EXECUTION: /health 200 shape; /predict missing file → 422 (FastAPI semantics, adapted from handoff's Django-400 expectation); corrupt bytes → 400 "Could not read image"; 503 branch driven by module global `model_loaded` (monkeypatchable); `_preprocess` deterministic (1,1,128,128) float32 in [-1,1]; `_load_background()` → (16,1,128,128) float32 in [-1,1], cached by identity.

#### Planned files to change (all new, additive only)
- backend/pytest.ini, backend/requirements-dev.txt, backend/tests/{conftest.py, test_health.py, test_predict_validation.py, test_predict_success.py, test_preprocess.py, test_integration_real_inference.py}

#### Files explicitly frozen
- backend/app/* (no production edits permitted), backend/model_weights.pt, backend/requirements.txt, backend/train_*.py, backend/prepare_brats.py, entire frontend/, root docs.

#### Test plan (summary)
- Health 200 exact key set; predict 422 (missing file) / 400 (corrupt, garbage-with-valid-extension) / 503 (patched model_loaded=False); mocked-XAI happy path asserting exact 7-key response, base64 PNG magic, label/confidence↔raw_probability consistency; shap-null path when DEMO_DATA_DIR missing; preprocessing determinism + independent normalization recomputation; background tensor shape/range/cache; one `@pytest.mark.slow` real-model end-to-end test. XAI mocked in `app.main` namespace; real model forward kept.
- Canonical commands: `cd backend && venv/Scripts/python.exe -m pytest`; root: `backend/venv/Scripts/python.exe -m pytest backend/tests -c backend/pytest.ini`; fast: `-m "not slow"`.

#### Risks
- pytest install needs network once; first collection ~15-40s (torch import); os.chdir in conftest is test-process-global; fixture depends on committed demo_data.

#### Rollback
- Delete new test files; purely additive, zero production impact.

#### Acceptance criteria
1. pytest green twice including slow test; 2. `git status` shows only the 8 new files, no modified existing files; 3. model SHA-256 unchanged; 4. API behavior identical to baseline; 5. no frontend changes.

#### Planner decision
READY FOR IMPLEMENTATION

## Implementor Record

### Implementor Record — Phase 0

**Session ID:** PHASE-0-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 628cd7c
**Ending commit:** (phase files left uncommitted for review; committed by orchestrator after APPROVED)
**Branch:** main

#### Planner record followed
- yes, exactly; no deviations.

#### Files changed (all new)
- backend/pytest.ini, backend/requirements-dev.txt, backend/tests/{conftest.py, test_health.py, test_predict_validation.py, test_predict_success.py, test_preprocess.py, test_integration_real_inference.py}

#### Functional changes
- None (purely additive test suite; production behavior untouched).

#### Tests added
- 13 tests: health 1, predict validation 4 (422 missing-file, 400 corrupt, 400 garbage-with-valid-extension, 503 not-loaded), mocked-XAI happy path 3 (exact 7-key shape + PNG magic, label/confidence↔raw_probability consistency, shap-null fallback), preprocess/background 4, real-inference integration 1 (`slow`, no mocks).

#### Commands executed
```text
backend/venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
cd backend && ./venv/Scripts/python.exe -m pytest   (run twice)
```
(pytest 8.4.2 installed; httpx2 2.13.1 already present.)

#### Test results
```text
Run 1: 13 passed in 3.28s
Run 2: 13 passed in 2.75s   (stability confirmed)
```

#### Frontend build result
```text
Not rebuilt (no frontend changes; baseline build captured at bootstrap: vite 8, OK)
```

#### Migration result
```text
N/A — no database in this architecture
```

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (untouched; never written)

#### Deviations from plan
- none

#### Unresolved items
- none

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 0

**Session ID:** PHASE-0-REVIEWER (orchestrator-dispatched independent subagent; did not trust implementor report)
**Reviewed commit:** 628cd7c (working tree, uncommitted phase files)
**Expected baseline commit:** 628cd7c

#### Diff independently inspected
- `git status --porcelain -uall`: exactly 8 new files + orchestrator's ledger edit; `git diff` of all production paths empty; nothing staged; HEAD unchanged at 628cd7c.

#### Architecture integrity
- PASS — zero production/frontend edits; no conftest outside backend/tests/; no import hooks; pytest.ini pytest-only.

#### API compatibility
- PASS — production diff empty; runtime behavior provably identical.

#### Database/migration safety
- PASS/N-A — no database layer exists.

#### Model integrity
- PASS — baseline 5f191bc8…b7bc1 == current 5f191bc8…b7bc1 (reviewer recomputed).

#### Automated tests rerun
```text
Run 1: 13 passed in 3.09s (includes slow, 0 skipped/deselected; -v cross-checked)
Run 2: 13 passed in 3.27s
```

#### Frontend build rerun
- Not rebuilt (untouched; verified via git status).

#### Manual regression performed
- Line-by-line audit of all 6 test modules against app/main.py: assertions confirmed substantive (exact key sets, FastAPI 422 detail structure, real model forward retained with only the three XAI functions patched in app.main namespace, normalization recomputed independently, cache identity, PNG magic on all image fields). No vacuous tests found.

#### Blocking findings
- none

#### Non-blocking findings
- Label-consistency test uses 6-dp-rounded raw_probability (theoretical 5e-7 boundary, zero practical flake risk); conftest os.chdir is process-global for tests only; untracked pytest caches verified gitignored; slow test doesn't re-assert label consistency (covered by mocked test).

#### Decision
APPROVED WITH NON-BLOCKING NOTES

#### Required next action
- Orchestrator commits the 8 phase files as the phase-0 commit; proceed to Phase 1.

## Gate Decision

**Decision:** APPROVED (with non-blocking notes)
**Phase 1 may start:** YES
**Committed as:** phase-0 commit (see Git history)

---

# Phase 1 — Documentation & Hygiene

## Planner Record

### Planner Record — Phase 1

**Session ID:** PHASE-1-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 2996163 (phase-0 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Repository state verified
- HEAD 2996163; tree clean; pytest 13/13 pass; npm build OK (re-verified by planner).
- demo_data/brain_tumor_dataset byte-identical duplicate of demo_data/no+yes (8.9 MB), diff -rq verified; intentional user commit 4d0f5ed; never read at runtime (main.py:66 reads only tumor/yes/notumor/no at demo_data top level).
- README problems: P1 stale "synthetic tumor/notumor" claim (README:34); P2 quickstart upload paths tumor/|notumor/ don't exist (README:91); P3 tree root name (README:28); P4 tree missing tests/; P5 LICENSE referenced but missing (README:123); P6 duplicate dataset undocumented.
- App.jsx blob-URL leak (App.jsx:43, no revokeObjectURL anywhere).
- .gitignore missing .history/ and brats_prepared/ (prepare_brats.py:53 generates it).
- N/A verified: requirements.txt already valid; no "lesion region"/summary text anywhere; no "AI Summary"; no "securely stored" (no history feature).

#### Planned changes
- frontend/src/App.jsx: add useEffect import + effect revoking previous preview blob URL on replacement/unmount (cleanup-after-commit pattern; handleFile untouched).
- README.md: root name, demo_data tree comment, add tests/ line, quickstart yes/no paths, Data assets note documenting duplicate copy, (LICENSE ref becomes true).
- .gitignore: add .history/ and brats_prepared/.
- LICENSE: new MIT file, "Copyright (c) 2026 NeuroScan XAI Authors" (placeholder, user-adjustable — ledger note).

#### Files frozen
- All backend production code, model, tests, demo_data, control docs (see plan).

#### API impact
- None.

#### Discovered & deferred
- train_demo.py:95-98 crashes if run with shipped demo_data (skips generation, DemoDataset expects notumor/) → Phase 2+ backend fix candidate.
- Duplicate dataset deletion → user decision, documented in README only.
- App.jsx:17 "exact input feature attributions" wording nit → out of Phase 1 scope.

#### Test plan
- pytest 13/13; npm run build; git status shows exactly README.md, .gitignore, LICENSE (new), App.jsx.

#### Planner decision
READY FOR IMPLEMENTATION

## Implementor Record

### Implementor Record — Phase 1

**Session ID:** PHASE-1-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 2996163
**Ending commit:** (committed by orchestrator after APPROVED)
**Branch:** main

#### Planner record followed
- yes; no deviations. (Tree line for tests/ placed as backend-level sibling of app/, matching actual layout — more accurate than the plan's suggested position inside the app/ block.)

#### Files changed
- README.md (5 doc corrections), .gitignore (+.history/, +brats_prepared/), frontend/src/App.jsx (useEffect import + blob-URL revocation effect; handleFile byte-identical), LICENSE (new MIT file).

#### Functional changes
- No behavior change except frontend blob-URL lifecycle: previous preview URL revoked after replacement commit; active URL revoked on unmount.

#### Tests added
- None (Phase 0 suite must still pass — it does).

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest
cd frontend && npm run build
git status --porcelain / git diff frontend/src/App.jsx
```

#### Test results
```text
13 passed in 3.43s
vite build: ✓ 17 modules transformed, built in 226ms
```

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (untouched)

#### Deviations from plan
- none (see planner-record note re tree line placement)

#### Unresolved items
- LICENSE copyright holder is a placeholder ("NeuroScan XAI Authors") — user-adjustable.

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 1

**Session ID:** PHASE-1-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** 2996163 (working tree, uncommitted phase files)
**Expected baseline commit:** 2996163

#### Diff independently inspected
- Changed set exactly {.gitignore, README.md, frontend/src/App.jsx, LICENSE(new)} + orchestrator ledger edit; backend/tests/data/requirements untouched (verified with porcelain + name-status + strip-trailing-cr content comparison vs git show 2996163).

#### Architecture integrity
- PASS — no production backend change; frontend change is a 2-hunk lifecycle fix.

#### API compatibility
- PASS — /health and /predict behavior unchanged; fetch flow byte-identical.

#### Database/migration safety
- N/A.

#### Model integrity
- PASS — sha256 recomputed: 5f191bc8…b7bc1 exact; file tracked, not ignored.

#### Automated tests rerun
```text
13 passed in 3.34s
```

#### Frontend build rerun
```text
vite v8.1.5: ✓ 17 modules transformed; built in 118ms
```

#### Manual regression performed
- Fact-checked every README statement (counts 98/155, byte-identical duplicates via diff -r, runtime-never-read claim vs main.py:56-82, remaining tumor/notumor mentions legitimate); verified React effect cleanup ordering (replacement revoke happens after DOM commit; StrictMode-safe; null-guard); git check-ignore confirms brats_prepared/ covered and model_weights.pt NOT ignored.

#### Blocking findings
- none

#### Non-blocking findings
- Duplicate-path wording relative to backend/demo_data/ could be more explicit; ~8.9 MB rounding (on-disk 8.84 MiB vs apparent 8.67 MB); LICENSE holder placeholder; ledger line-ending normalization warning (pre-existing repo-wide).

#### Decision
APPROVED WITH NON-BLOCKING NOTES

#### Required next action
- Commit phase-1; proceed to Phase 2 (candidate backend items carried: train_demo.py crash with shipped demo_data; upload validation; inference robustness).

## Gate Decision

**Decision:** APPROVED (with non-blocking notes)
**Phase 2 may start:** YES
**Committed as:** phase-1 commit (see Git history)

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

### Planner Record — Phase 2

**Session ID:** PHASE-2-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 1f72ab7 (phase-1 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Current behavior confirmed (by inspection + execution)
- /predict has NO extension/MIME/size validation; garbage with valid extension fails only at PIL; raw exception text leaks in 400 detail; `await file.read()` buffers unbounded; `async def` + CPU-bound work serializes on the event loop (accidental safety, no lock); starlette 1.6.0 populates `UploadFile.size` (verified in installed source) enabling pre-read size checks.
- SHAP/device handling verified already correct (xai.py:121-122 moves input+background to device; `.to(device)` never mutates the CPU cache) → N/A, no change.
- train_demo.py:95 crashes with shipped Kaggle-layout demo_data (generation gated on demo_data absence; DemoDataset expects tumor/notumor).
- Frontend drag-drop bypasses `accept` attribute → backend allowlist is the real gate.

#### Planned changes
- NEW backend/app/config.py: IMG_SIZE=128, MAX_UPLOAD_MB (env, default 10), MAX_UPLOAD_BYTES, ALLOWED_IMAGE_EXTENSIONS={.png,.jpg,.jpeg}.
- backend/app/main.py: import config constants (IMG_SIZE stays importable from app_main); add logging + threading.Lock `_inference_lock`; extension check pre-read (400 "Unsupported file type..."); pre-read size check via file.size (413, message derives MAX_UPLOAD_MB); post-read fallbacks (len>MAX → 413, empty → 400 "Empty file uploaded."); lock wraps _preprocess→response construction (no await inside; 503 check + read outside); sanitized 400: logger.exception + "Invalid or unreadable image file.".
- backend/train_demo.py: generation gate → generate when tumor/ or notumor/ missing (3-line change).
- Tests: NEW backend/tests/test_predict_upload_validation.py (8 tests: unsupported ext 400, no ext 400, oversize 413, configurable limit 413, empty 400, valid png 200 mocked-XAI, lock exists + predict works, no-internal-leak assertion); Phase 0 test_predict_validation.py: ONLY two detail assertions change to the sanitized message.
- Frozen: model.py, xai.py, train_real.py, prepare_brats.py, checkpoint, frontend, conftest, pytest.ini.

#### API impact (error matrix)
- 400 "Unsupported file type. Allowed: .png, .jpg, .jpeg." (NEW); 413 "Uploaded file is too large. Maximum size is 10 MB." (NEW); 400 "Empty file uploaded." (NEW, was generic parse 400); corrupt-content 400 text CHANGED to "Invalid or unreadable image file."; success path + /health byte-identical; 422/503 unchanged. .bmp rejected deliberately (frontend contract is png/jpeg); uppercase extensions accepted.

#### Key planner decisions
1. Lock = threading.Lock with async def kept (option a) — converts accidental event-loop serialization into enforced safety; zero behavior change; no threadpool migration.
2. Allowlist {.png,.jpg,.jpeg} case-insensitive.
3. Pre-read file.size check + post-read len fallback; MAX_UPLOAD_MB env-configurable.
4. config.py minimal, app-side only; training-script IMG_SIZE duplication judged harmless (frozen by checkpoint + Phase 0 tests).
5. train_demo.py fix included (out-of-the-box crash, no inference impact).

#### Risks
- Previously-"working" odd-filename clients now rejected (deliberate); file.size None handled by fallback; no deadlock (no await in critical section, single non-nested lock); pytest captures ERROR logs harmlessly; after train_demo runs, demo_data gains tumor/notumor dirs which _load_background will prefer (pre-existing intended behavior from 628cd7c).

#### Rollback
- Single revert of phase-2 commit.

#### Acceptance criteria
1. 21/21 pytest (13 existing, 2 assertion lines changed as documented, 8 new); 2. manual curl matrix (txt→400, >10MB→413, empty→400, mri.JPG→200, success shape identical); 3. no `{e}` leak remains in main.py 4xx details; 4. lock guards _preprocess→response, read+503 outside; 5. train_demo.py starts cleanly with shipped demo_data, yes/no untouched; 6. checkpoint SHA, endpoints, response fields, preprocessing unchanged; frontend builds.

#### Planner decision
READY FOR IMPLEMENTATION

## Implementor Record

### Implementor Record — Phase 2

**Session ID:** PHASE-2-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 1f72ab7
**Ending commit:** (committed by orchestrator after APPROVED)
**Branch:** main

#### Planner record followed
- yes; two justified minor deviations: (1) MAX_UPLOAD_MB included in the config import line (plan's own 413 message needs it); (2) lock-existence assertion uses `isinstance(x, type(threading.Lock()))` because `threading.Lock` is a factory function in CPython 3.10 and direct isinstance raises TypeError (verified empirically).

#### Files changed
- NEW backend/app/config.py; backend/app/main.py (validation chain + lock + sanitized errors + config import); backend/train_demo.py (3-line generation-gate fix); backend/tests/test_predict_validation.py (2 detail assertions only); NEW backend/tests/test_predict_upload_validation.py (8 tests).

#### Functional changes
- /predict now rejects: unsupported/missing extension (400, pre-read), oversize >MAX_UPLOAD_BYTES (413, pre- and post-read), empty body (400). Corrupt-content 400 detail sanitized ("Invalid or unreadable image file.") with logger.exception server-side. threading.Lock guards _preprocess→response (no await inside; 503 check + read outside). Success path and /health byte-identical. train_demo.py no longer crashes out-of-the-box with shipped Kaggle-layout demo_data.

#### Tests added
- 8 (unsupported ext 400, no ext 400, >10MB 413, configurable-limit 413, empty 400, valid-png 200 with exact keys + PNG magic under mocked XAI + real forward, lock existence + working predict, no-leak detail).

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest   (twice)
python one-liner gate verification (no training run)
```

#### Test results
```text
Run 1: 21 passed in 3.28s
Run 2: 21 passed in 3.05s
```

#### Frontend build result
- Not rebuilt (frontend untouched).

#### Migration result
- N/A.

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (untouched)

#### Deviations from plan
- Only the two noted above.

#### Unresolved items
- none

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 2

**Session ID:** PHASE-2-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** 1f72ab7 (working tree, uncommitted phase files)
**Expected baseline commit:** 1f72ab7

#### Diff independently inspected
- Changed set exactly {config.py(new), main.py, train_demo.py, test_predict_validation.py, test_predict_upload_validation.py(new)} + ledger; frozen set (model.py, xai.py, train_real.py, prepare_brats.py, requirements.txt, conftest.py, pytest.ini, frontend/) zero-diff.

#### Architecture integrity
- PASS — validation order verified line-by-line; extension rejection occurs before any body read; lock critical section contains zero awaits and excludes 503 check + read; HTTPException inside with-block provably releases lock (verified live); success payload compared byte-for-byte vs git show 1f72ab7.

#### API compatibility
- PASS — new error matrix correct (400 unsupported/empty/sanitized, 413 oversize, 422/503 unchanged, success path identical).

#### Database/migration safety
- N/A.

#### Model integrity
- PASS — sha256 recomputed 5f191bc8…b7bc1.

#### Automated tests rerun
```text
Run 1: 21 passed in 2.85s
Run 2: 21 passed in 3.74s
```

#### Frontend build rerun
- Not rebuilt (frontend untouched).

#### Manual regression performed
- Acceptance matrix with real unmocked forward: mri.JPG (uppercase) → 200; corrupt.png → 400 sanitized detail; empty.png → 400; >10MB → 413; scan.txt → 400 unsupported; exactly-10MB boundary passes size gate (strict >). Env override MAX_UPLOAD_MB=3 verified (3145728). train_demo side effect confirmed as pre-existing intended _load_background ordering from 628cd7c, not a regression.

#### Blocking findings
- none

#### Non-blocking findings
- Framework-level multipart parsing buffers body before endpoint (platform reality; application-level claim correctly scoped); lock keeps XAI on event loop (documented planner decision, threadpool offload is future headroom); pre-read file.size check is fast-path with post-read fallback as real enforcement.

#### Decision
APPROVED

#### Required next action
- Commit phase-2; proceed to Phase 3A (Evaluation & Reliability framework).

## Gate Decision

**Decision:** APPROVED
**Phase 3A may start:** YES
**Committed as:** phase-2 commit (see Git history)

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

### Planner Record — Phase 3A

**Session ID:** PHASE-3A-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** dbf4aea (phase-2 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Current state verified
- HEAD dbf4aea; 21 tests pass. matplotlib 3.10.9 present transitively via captum; sklearn 1.7.2, numpy 2.2.6. _preprocess lives in app/main.py (module import has model-loading side effect). demo_data/yes=155, no=98; brain_tumor_dataset duplicate is a CHILD dir of demo_data → name-based immediate-child class mapping excludes it.
- Production decision rules to mirror exactly: positive iff p >= threshold (0.5 inclusive); confidence = max(p, 1-p).

#### Planned changes
- NEW backend/app/preprocessing.py (preprocess_bytes — exact body moved from main.py); main.py delegates (behavior byte-identical; test_preprocess.py passes unmodified).
- NEW backend/evaluation/ package: metrics.py (pure functions: confusion [[TN,FP],[FN,TP]] rows=true, binary metrics, per-class one-vs-rest + macro/weighted, ECE 10-bin min(floor(p*10),9), Brier, confidence_analysis), evaluate.py (CLI: --data-dir --output-dir --threshold --batch --high-confidence --uncertain-low/high --model-path; loads model exactly like main.py; writes 12 artifacts incl. run_metadata.json with git commit + model sha256 + class counts + versions, predictions/per_class/confidence/calibration CSVs, confusion matrices PNG+JSON, reliability_diagram.png, EVALUATION_REPORT.md with limitations + non-clinical disclaimer).
- NEW tests: test_evaluation_metrics.py (synthetic known-value cases, orientation locks, zero-division conventions, sklearn cross-checks), test_evaluation_integration.py (slow, 4-image tmp dataset, wiring only, NO performance assertions).
- requirements.txt: +matplotlib>=3.7.0 (explicit declaration of transitive dep). .gitignore: +backend/evaluation_output/.

#### Metric definitions locked
- specificity = TN/(TN+FP); balanced acc = (recall+specificity)/2; per-class one-vs-rest, macro = unweighted mean, weighted = support-weighted; Brier = mean (p-y)^2; ECE = Σ (n_B/N)·|acc_B − conf_B| over 10 equal-width bins, bin = min(int(p*10), 9); zero-division → 0.0; uncertain band inclusive [0.4, 0.6] defaults; high-confidence error default ≥ 0.9.

#### ORCHESTRATOR CORRECTION to plan test vectors (recorded before implementation)
- Plan Case A expected ECE 0.275 is WRONG: correct value is 0.325 (gaps: |1-0.9|+|1-0.8|+|1-0.7|+|1-0.3|+|0-0.2|+|0-0.1|+|0-0.6|+|0-0.4| = 2.6, /8). Plan Case B was underspecified (exact y_score not given). Implementor instructed to independently re-derive EVERY expected value from the formulas and treat the formulas — not the plan's numbers — as normative; metric functions must never be tuned to match an incorrect expectation.

#### API impact
- None. /health and /predict response schema untouched; only main.py change is the preprocessing delegate.

#### Risks
- Delegate edit behavior drift (mitigated: pure move + unmodified test_preprocess.py recomputes normalization); ECE float edges (min(floor(p*10),9) locked by test with pytest.approx 1e-9); dataset double-counting (immediate-child mapping); zero-division convention fixed to 0.0 and cross-checked vs sklearn.

#### Rollback
- Single revert; 21-test baseline is the restore gate.

#### Acceptance criteria
1. 21 original tests unmodified + new tests green; 2. model sha unchanged; zero diff on model.py/xai.py/config.py; 3. docstring command runs end-to-end on demo_data producing all artifacts with counts yes=155/no=98; 4. known-value metric tests pass exactly; 5. evaluation run leaves git status clean (output dir ignored).

#### Planner decision
READY FOR IMPLEMENTATION (with orchestrator's test-vector correction above)

## Implementor Record

### Implementor Record — Phase 3A

**Session ID:** PHASE-3A-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** dbf4aea
**Ending commit:** (committed by orchestrator after APPROVED)
**Branch:** main

#### Planner record followed
- yes; noted deviations: (1) Case B concrete vector substituted (orchestrator's example had a false positive at t=0.5); Brier 0.075 / ECE 0.25 derived; (2) run_evaluation re-exported lazily (PEP 562) to avoid a RuntimeWarning under `python -m evaluation.evaluate`; (3) unused io/PIL imports removed from main.py; (4) calibration_data.csv lists all 10 bins incl. empty.
- ORCHESTRATOR CORRECTION applied: Case A ECE asserted at 0.325 (plan's 0.275 was wrong); one real bug found during testing (compute_brier mis-unpacking) and fixed — no metric was ever tuned toward an expected number.

#### Files changed
- NEW: backend/app/preprocessing.py; backend/evaluation/{__init__.py, metrics.py, evaluate.py}; backend/tests/test_evaluation_metrics.py (15 tests); backend/tests/test_evaluation_integration.py (1 slow test).
- MODIFIED: backend/app/main.py (delegate; unused imports removed), backend/requirements.txt (+matplotlib>=3.7.0), .gitignore (+backend/evaluation_output/).

#### Functional changes
- None to inference: preprocessing body moved verbatim to app/preprocessing.py; main.py delegates. New standalone evaluator reusing production model/preprocessing exactly; 12 artifacts; gitignored output dir.

#### Tests added
- 16 (15 known-value metric tests with derivation comments + sklearn cross-checks + orientation lock; 1 slow 4-image end-to-end wiring test without performance assertions). Total suite: 37.

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest   (3 green runs)
cd backend && ./venv/Scripts/python.exe -m evaluation.evaluate --data-dir demo_data --output-dir evaluation_output
```

#### Test results
```text
37 passed in 4.86s (final; three consecutive green runs)
```

#### Smoke run (NOT final evaluation results — Phase 3B governs)
- 253 images, ~11s CPU. run_metadata: commit dbf4aea, model sha 5f191bc8…b7bc1, class_counts {no:98, yes:155}. Indicative metrics: accuracy 0.6126, precision 0.7664, recall 0.5290, specificity 0.7449, F1 0.6260, balanced acc 0.6370, ECE 0.2907, Brier 0.3129; confusion [[73,25],[73,82]] (internally consistent). These figures are smoke-run output only and MUST NOT be cited as final model performance.

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Deviations from plan
- The four noted above.

#### Unresolved items
- none

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 3A

**Session ID:** PHASE-3A-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** dbf4aea (working tree, uncommitted phase files)
**Expected baseline commit:** dbf4aea

#### Diff independently inspected
- Changed set exactly as claimed; frozen files zero-diff (verified per-file); preprocessing.py body byte-equivalent to old _preprocess; main.py /health + /predict logic and payload byte-identical.

#### Metric implementation audit (math independently re-derived BEFORE running code)
- Reviewer hand-derived every case, then ran the functions: all match (Case A 0.75×6/0.15/0.325/[[3,1],[1,3]]; Case C zero-division conventions; Case D 0.4625/0.406875/bin9; t=0.65 0.875/1.0/0.75/6-7; Case 7 0.75 mean/2/2). Code audit confirms normative formulas incl. min(int(p*10),9) binning (float subtlety 0.7*10==7.0 verified in venv), zero-division→0.0, [[TN,FP],[FN,TP]] orientation, inclusive threshold/band. Edge probes: empty inputs, p=1.0, empty bins/groups. sklearn cross-checks pass. No tuning of functions to expectations.

#### Architecture integrity
- PASS — no inference-behavior change; evaluator reuses app.model + app.preprocessing + app.config (no copy-paste); matplotlib Agg; no torch imports in metrics.py.

#### API compatibility
- PASS — API surface byte-identical; all 21 original tests unmodified and green.

#### Database/migration safety
- N/A.

#### Model integrity
- PASS — sha256 independently recomputed: 5f191bc8…b7bc1.

#### Automated tests rerun
```text
Run 1: 37 passed in 4.10s
Run 2: 37 passed in 4.14s
```

#### End-to-end verification
- Reviewer ran the evaluator into a temp dir: 12 artifacts; 253 predictions; class_counts {no:98, yes:155}; metadata commit/sha correct; internal consistency recomputed from artifacts (confusion sums, accuracy from cm, ECE from calibration CSV = 0.2906901 matching metrics.json; misclassified = 98 = FP+FN); threshold rule verified on all rows. Temp dir cleaned up.

#### Blocking findings
- none

#### Non-blocking findings
- per_class_metrics.csv "support" column holds N for macro/weighted rows (cosmetic); class_counts keyed by raw dir name (case-sensitive; demo_data lowercase so no impact); uncertain band defined on raw p (documented convention); metrics.json minor redundancy.

#### Decision
APPROVED

#### Required next action
- Commit phase-3a; Phase 3B may proceed (dataset approval is the next gate).

## Framework Gate

```text
FRAMEWORK STATUS: APPROVED
DATASET STATUS: PENDING
RESULT STATUS: PENDING DATASET
```

**Phase 4 may start:** YES (framework approved; 3B can execute in parallel/after)

A framework can be approved even when the independent dataset is not yet available.

Required approved state before Phase 4:

```text
FRAMEWORK STATUS: APPROVED
```

---

# Phase 3B — Independent Evaluation Execution

> Conditional. Run when an approved labeled independent dataset is available.

## Dataset Approval Record

```text
Dataset name: bundled Kaggle "brain_tumor_dataset" (classic 253-image brain MRI collection)
Source: bundled in-repo; introduced in commit 4d0f5ed "Added original datasets"
Version/release: NOT RECORDED in repo — external URL, uploader, and release identifier unknown
  (verification note: identification as the widely-circulated 253-image Kaggle brain MRI set is
  consistent with, but not proven by, repository evidence)
License/use notes: not stated in repo; research/demonstration use only, non-clinical
Local path: backend/demo_data/ (classes yes/ = 155 tumour, no/ = 98 normal; sibling
  brain_tumor_dataset/ is an excluded byte-identical duplicate, cmp-verified)
Manifest: docs/evaluation/dataset_manifest.txt (algorithm: immediate children of yes/ and no/
  only, image extensions, sorted relative paths with forward slashes, lines
  "<sha256-hex>  <relative-path>", UTF-8 LF)
Manifest SHA-256: (recorded in EVAL-001 after generation)
Sample count: 253
Class counts: yes=155, no=98
Independence evidence: (1) checkpoint backend/model_weights.pt arrived in commit e09d305,
  BEFORE the dataset commit 4d0f5ed (planner correction: initial commits be19683..fc2e8bb
  carried a SYNTHETIC notumor/tumor layout; the Kaggle yes/no set arrived only at 4d0f5ed);
  (2) train_real.py reads only brats_prepared/ (absent from repo — training external);
  (3) train_demo.py trains on generated synthetic images only; (4) no retraining since e09d305
  (checkpoint byte-identical, sha 5f191bc8…b7bc1); (5) evaluator scans demo_data non-recursively
  and excludes the duplicate dir by construction
Known overlap risk: (a) DOMAIN SHIFT — checkpoint trained on BraTS 2021 FLAIR-style prepared
  slices, dataset is clinical-style Kaggle MRI; depressed absolute numbers are an expected
  finding and must not be generalized; (b) 16 dataset images are sampled as SHAP background at
  inference (torch.no_grad, no weight updates) — disclosed and accepted; (c) external overlap
  of the Kaggle corpus with BraTS or other sets is unverifiable from the repo — unverified
Approved by: orchestrator per autonomous mandate (user may revoke/adjust)
Approval date: 2026-09-25
Status: APPROVED WITH DISCLOSURES
```

## Planner Record

### Planner Record — Phase 3B

**Session ID:** PHASE-3B-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 58de4ed (phase-3a commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (re-verified)

#### Verified findings
- Dataset composition and byte-identity of the duplicate confirmed via per-file cmp (253 files).
- PROVENANCE CORRECTION recorded (see approval record): yes/no Kaggle set arrived at 4d0f5ed,
  replacing the synthetic layout from initial commits; checkpoint predates the dataset commit.
- Evaluator scan_dataset non-recursive, deterministic (sorted dirs+files, eval mode, no_grad,
  CPU-only torch build); .gitignore gap identified: anchored pattern backend/evaluation_output/
  does NOT cover evaluation_output_official/ → official runs use evaluation_output/official and
  evaluation_output/repro subdirs (zero frozen-file changes).
- Timestamp-bearing artifacts: metrics.json (generated_at), run_metadata.json
  (generated_at_utc), EVALUATION_REPORT.md (Generated line). All others timestamp-free.

#### Official run protocol
- Pre-flight: HEAD==58de4ed; backend/frontend clean; model sha verified; 37/37 pytest.
- Run 1 official: `cd backend && venv/Scripts/python.exe -m evaluation.evaluate --data-dir demo_data --output-dir evaluation_output/official`
- Run 2 repro (independent process): `... --output-dir evaluation_output/repro`
- Reproducibility gate (MANDATORY acceptance): Run 2 byte-identical (sha256) on predictions.csv,
  misclassified_cases.csv, per_class_metrics.csv, confidence_analysis.csv, calibration_data.csv,
  confusion_matrix.json; metrics.json/run_metadata.json/report identical modulo timestamps; PNG
  shas recorded (soft). ANY difference → BLOCK, do not record results.
- Threshold 0.5 primary only; sensitivity analysis noted as limitation.
- Curated snapshot → new docs/evaluation/: EVALUATION_REPORT.md (with header block: commit,
  model sha, manifest sha, approval date, smoke-supersession note), metrics.json,
  run_metadata.json, confusion_matrix.json, per_class_metrics.csv, confidence_analysis.csv,
  predictions.csv, both confusion PNGs, reliability_diagram.png, dataset_manifest.txt
  (~253 lines). Raw outputs stay gitignored.

#### Documentation guardrails
- Numbers only in docs/evaluation/* and ledger EVAL-001 at this phase; README frozen until
  Phase 7 (which must reference docs/evaluation/); frontend must carry no performance claims
  (verified clean); smoke-run figures remain non-citable; all results text carries the
  non-clinical disclaimer.

#### Files to change
- docs/evaluation/* (new), PROJECT_EXECUTION_LEDGER.md (orchestrator). Nothing in
  backend/ or frontend/. .gitignore fallback line only if output-dir naming changes (not needed).

#### Risks
- Determinism failure → hard BLOCK; raw-output leakage (mitigated by subdir naming);
  CRLF/LF pinning for the manifest (record sha of file as written); provenance overstatement
  (forbidden — verification note recorded); poor absolute metrics under domain shift are a
  legitimate finding reported verbatim; run_metadata records HEAD only — tree condition stated
  in report header.

#### Rollback
- rm -r docs/evaluation/ + revert phase-3b commit; no code/data/model changes to unwind.

#### Acceptance criteria
1. Pre-flight passes; 2. all 12 artifacts written by Run 1; 3. reproducibility gate PASSES; 4.
  manifest exists (253 file lines) with sha recorded; 5. curated snapshot present with annotated
  header; 6. EVAL-001 fully populated (binary per-class no/yes) with review PENDING; 7. post-phase
  git status shows only docs/evaluation/ + ledger; no README/frontend changes.

#### Planner decision
PROCEED

## Implementor / Evaluation Run Record

### Implementor Record — Phase 3B (execution only; no code changes)

**Session ID:** PHASE-3B-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 58de4ed
**Branch:** main

#### Files changed
- NEW docs/evaluation/: EVALUATION_REPORT.md (official report + EVAL-001 header block), dataset_manifest.txt, metrics.json, run_metadata.json, confusion_matrix.json, per_class_metrics.csv, confidence_analysis.csv, predictions.csv, confusion_matrix_counts.png, confusion_matrix_normalized.png, reliability_diagram.png. No backend/frontend changes.

### Evaluation Run EVAL-001

**Date:** 2026-09-25
**Git commit:** 58de4ed3ca1ae0fbd6ffecee901dfaa50751d284 (phase-3a; working tree beyond it contained only control-document/doc additions)
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1
**Dataset:** bundled Kaggle brain_tumor_dataset @ commit 4d0f5ed (APPROVED WITH DISCLOSURES 2026-09-25)
**Dataset manifest SHA-256:** ca502c2b8443b0d6d854578cf085caf02e54a2fffb9db02885abc6a17e343335 (docs/evaluation/dataset_manifest.txt, 253 file lines)
**Sample count:** 253
**Class counts:** no=98, yes=155
**Device:** cpu (torch 2.13.0+cpu)
**Output directory:** backend/evaluation_output/official (raw, gitignored); curated snapshot docs/evaluation/

#### Commands
```text
# pre-flight: git rev-parse HEAD / git status / sha256 model / pytest (37 passed)
cd backend && ./venv/Scripts/python.exe -m evaluation.evaluate --data-dir demo_data --output-dir evaluation_output/official
cd backend && ./venv/Scripts/python.exe -m evaluation.evaluate --data-dir demo_data --output-dir evaluation_output/repro
```

#### Reproducibility check
- Run 2 (independent process) byte-identical to Run 1 on all timestamp-free artifacts
  (predictions.csv, misclassified_cases.csv, per_class_metrics.csv, confidence_analysis.csv,
  calibration_data.csv, confusion_matrix.json) AND all three PNGs; metrics.json,
  run_metadata.json, EVALUATION_REPORT.md identical modulo timestamp fields. GATE: PASS.

#### Required artifacts
- [x] run_metadata.json — [x] predictions.csv — [x] metrics.json — [x] per_class_metrics.csv
- [x] confusion_matrix.json — [x] confusion_matrix_counts.png — [x] confusion_matrix_normalized.png
- [x] confidence_analysis.csv — [x] misclassified_cases.csv (raw output only, per plan)
- [x] EVALUATION_REPORT.md (curated + header) — [x] reliability_diagram.png — [x] calibration_data.csv (raw output only)

#### Mandatory metrics (binary adaptation; threshold 0.5, positive = tumour)
```text
accuracy: 0.6126
macro precision: 0.6332
macro recall: 0.6370
macro F1: 0.6122
macro specificity (one-vs-rest, = balanced accuracy): 0.6370
binary specificity (negative class): 0.7449
weighted precision: 0.6632
weighted recall: 0.6126
weighted F1: 0.6153
```

#### Per-class metrics
```text
no  (normal):  precision 0.5000, recall 0.7449, F1 0.5984, support 98
yes (tumour):  precision 0.7664, recall 0.5290, F1 0.6260, support 155
```

#### Confusion matrix (rows = true [no, yes], cols = predicted)
```text
counts      [[73, 25], [73, 82]]
normalized  [[0.7449, 0.2551], [0.4710, 0.5290]]
```

#### Reliability outputs
```text
correct mean confidence: 0.9041
incorrect mean confidence: 0.8624
high-confidence error count (conf >= 0.9): 55
uncertain count (0.4 <= p <= 0.6): 19
ECE (10 equal-width bins, min(int(p*10),9)): 0.2907
Brier score: 0.3129
balanced accuracy: 0.6370
```

#### Limitations
- Non-clinical, research demonstration only; not a diagnostic tool.
- DOMAIN SHIFT: checkpoint trained on BraTS 2021 FLAIR-style prepared slices; evaluated on
  clinical-style Kaggle MRI. Absolute numbers reflect this shift and must not be generalized.
- Single-dataset evaluation; no external holdout; dataset external provenance/license unrecorded.
- Results valid at decision threshold p >= 0.5 only (evaluator supports --threshold for
  future sensitivity analysis).
- 16 dataset images serve as SHAP background at inference (no_grad, no weight updates) — disclosed.
- Phase 3A smoke-run figures were indicative only and are superseded by EVAL-001.

#### Independent results review
PENDING

## Independent Results Reviewer Record

### Independent Results Reviewer Record — Phase 3B / EVAL-001

**Session ID:** PHASE-3B-RESULTS-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** 58de4ed (working tree with docs/evaluation/ + ledger)
**Expected baseline commit:** 58de4ed

#### Independent verification performed
- Recomputed EVERY claimed metric from docs/evaluation/predictions.csv with own stdlib-only
  code (no repo code imported): all exact/within 1e-3 of claimed (confusion [[73,25],[73,82]]
  exact; accuracy 0.612648; per-class and macro/weighted P/R/F1; binary specificity 0.744898;
  balanced accuracy 0.636965; ECE 0.290690; Brier 0.312933; mean confidences; 55 high-conf
  errors; 19 uncertain). Threshold rule verified on all 253 rows (0 mismatches).
- Dataset manifest independently rebuilt with own code: byte-identical, sha256
  ca502c2b8443b0d6d854578cf085caf02e54a2fffb9db02885abc6a17e343335 == claimed == snapshot file.
- Run independently reproduced into a temp dir: byte-identical on all timestamp-free artifacts
  and PNGs; metrics/metadata/report equal modulo timestamps. Temp cleaned; repo state unchanged.
- Guardrails: no performance figures in frontend/ or README.md (grep sweep). Ledger EVAL-001
  matches recomputed values; mandatory limitation wording present.

#### Blocking findings
- none

#### Non-blocking findings
- predictions.csv uses Windows backslash paths while manifest uses forward slashes (each
  internally consistent, documented); ~2e-8 ECE/Brier difference between 6-dp CSV recomputation
  and full-precision metrics.json (expected); metrics.json timestamp 2026-09-24T22:09Z vs ledger
  date 2026-09-25 (timezone); honest performance observations (modest accuracy 0.61, ECE 0.29
  overconfidence, 55/98 errors at >=0.9 confidence, class-no precision 0.5) — all disclosed in
  the report Limitations.

#### Decision
APPROVED WITH NON-BLOCKING NOTES

#### Required next action
- Commit phase-3b; proceed to Phase 4.

## Results Gate

```text
DATASET STATUS: APPROVED (with disclosures)
DATASET INDEPENDENCE: VERIFIED
RESULT STATUS: GENERATED AND REVIEWED (EVAL-001 APPROVED WITH NON-BLOCKING NOTES)
```

No model-performance figures may be represented as final while this gate is pending.

---

# Phase 4 — Scan Metadata, Report & PDF

## Planner Record

### Planner Record — Phase 4

**Session ID:** PHASE-4-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** adbc019 (phase-3b commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (re-verified)

#### Adaptation note (per CORRECTION C-001)
Handoff Feature C assumes an existing history/scan-detail page and SQLite Scan records. This
repo has none, so Phase 4 BUILDS the substrate additively: SQLite persistence + history API +
scan-detail report page + multipage client-side PDF export on the frozen FastAPI/React stack.

#### Binding architecture decisions
- D1 stdlib sqlite3, connection-per-op + write lock; SCAN_DB_PATH global read at CALL time
  (tests monkeypatch app.db.SCAN_DB_PATH); schema lazily created; incompatible existing schema
  → RuntimeError surfaced as clean 500 "History storage error."
- D2 source dimensions via new image_dimensions() helper in preprocessing.py (preprocess_bytes
  untouched); D3 cached model_fingerprint(path) in new app/model_info.py; D4 processing_time_ms
  = perf_counter around lock section; DB insert moved OUTSIDE the inference lock.
- D5 /predict: original 7 fields byte-identical + additive fields on successful persistence;
  DB FAILURE → exact original 7-field payload with 200 (inference primary, history additive).
- D8 react-router-dom v7 with HashRouter (built dist works on any static server); D9 deps
  exactly react-router-dom, html2canvas@^1.4.1, jspdf@^2.5.2 (sanctioned by handoff Feature C);
  D11 PDF captures the dark theme as-rendered; D10 CSS appended to App.css only.
- GET /history = lightweight array newest-first WITHOUT image payloads/fingerprint;
  GET /history/{id} = full record; DELETE → 204. Field lists locked in the plan.

#### Files to change
- NEW backend: app/db.py, app/model_info.py, tests/{test_db, test_history_api, test_predict_persistence}.py
- MODIFIED backend: app/main.py (additive persistence + timing + docstring), app/preprocessing.py (image_dimensions only), tests/conftest.py (autouse isolated_scan_db fixture), 3 exact-key assertions → superset (test_predict_success.py:33, test_predict_upload_validation.py:98, test_integration_real_inference.py:26)
- NEW frontend: src/api.js, src/xaiMethods.js, src/pages/{Home,HistoryList,ScanDetail}.jsx, src/exportPdf.js
- MODIFIED frontend: App.jsx (shell + HashRouter + nav), App.css (Phase 4 section), package.json (+3 deps)
- ROOT: .gitignore (+neuroscan.db)
- Expected test total: 53. Frozen: model.py, xai.py, config.py, evaluation/, train_*, checkpoint, main.jsx, vite.config.js, requirements*.

#### Risks
- SCAN_DB_PATH must never be bound by value outside db.py; _schema_ready reset in fixture;
  JSONResponse restructure must keep all inference inside the lock; jspdf pinned major 2;
  html2canvas-safe CSS verified (no oklch/lab); react-router v7 import surface.

#### Planner decision
READY FOR IMPLEMENTATION

## Implementor Record

### Implementor Record — Phase 4

**Session ID:** PHASE-4-IMPLEMENTOR (orchestrator-dispatched independent subagent) + orchestrator fix-loop after review
**Starting commit:** adbc019
**Branch:** main

#### Planner record followed
- yes; deviations: fetchJson returns null on 204 (DELETE flow); ApiReadout extracted for StatusDot reflectivity; extra CSS helper classes in the Phase 4 block; formatBytes duplicated in two pages (no shared util planned); placeholder text generalized.

#### Files changed
- NEW backend: app/db.py, app/model_info.py, tests/{test_db,test_history_api,test_predict_persistence}.py (16 tests).
- MODIFIED backend: app/main.py (persistence + /history endpoints + docstring), app/preprocessing.py (image_dimensions only), tests/conftest.py (autouse isolated_scan_db), 3 exact-key→superset test edits.
- NEW frontend: src/{api.js,xaiMethods.js,exportPdf.js}, src/pages/{Home,HistoryList,ScanDetail}.jsx.
- MODIFIED frontend: App.jsx (HashRouter shell + nav + ApiReadout), App.css (appended Phase 4 section), package.json/lock (+react-router-dom 7.18.4, html2canvas 1.4.1, jspdf 2.5.2).
- ROOT: .gitignore (+neuroscan.db).

#### Reviewer fix-loop applied (orchestrator)
- All three /history handlers now wrap db calls in try/except → 500 detail "History storage error." (contract item previously unmet) + 3 new sanitized-500 tests.
- App shell StatusDot made reflectivity-real: ApiReadout probes GET /health on mount and on every route change (AbortController).

#### Tests added
- 19 total (16 from implementor + 3 from fix-loop). Suite: 56 passed.

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest        (multiple green runs; final 56 passed)
cd frontend && npm install react-router-dom html2canvas@^1.4.1 jspdf@^2.5.2
cd frontend && npm run build && npm run lint
Live browser verification: uvicorn :8000 + vite :5173, 3 rows seeded via /predict
```

#### Test results
```text
56 passed in 4.83s; vite build OK (jspdf/html2canvas code-split); oxlint 0 warnings 0 errors
```

#### Live browser verification (orchestrator, IAB)
- Home: baseline layout intact + new nav + green API dot. History: table newest-first, color-coded predictions, source dims correct, delete buttons. Scan detail (#/history/:id): full Feature-C metadata (id, timestamp, filename, MIME, source dims, size, model, fingerprint truncated+toggle, classes with detected highlighted, prediction incl. processing time), all 4 images incl. SHAP, methods + non-clinical disclaimer. Download PDF clicked → download event fired (jsPDF executed, no JS errors).

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Deviations from plan
- Listed above; none touch frozen files.

#### Unresolved items
- none

#### Implementor status
READY FOR REVIEW → reviewed; fix-loop applied → READY TO COMMIT

## Independent Reviewer Record

### Independent Reviewer Record — Phase 4

**Session ID:** PHASE-4-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** adbc019 (working tree, uncommitted phase files)
**Expected baseline commit:** adbc019

#### Diff independently inspected
- Changed set exactly as claimed; frozen set verified zero-diff per file (model.py, xai.py, config.py, evaluation/**, train_*, requirements*, pytest.ini, 4 existing test files, main.jsx, vite.config.js, index.html, index.css); checkpoint untouched.

#### Architecture integrity
- PASS — db.py: call-time SCAN_DB_PATH reads, finally-closed connections, double-checked _schema_ready, PRAGMA validation of the 17 columns, sequential (never nested) write lock; main.py: original 7 payload keys byte-identical semantics, all inference inside lock, JSONResponse + DB insert outside, DB-failure → exact original 7-field 200.

#### API compatibility
- PASS — /health byte-identical; /predict superset per contract; /history 11 lightweight keys; 404/204 correct. Note: reviewer found the planned "History storage error." 500 detail MISSING → fixed in the implementor fix-loop (try/except added to all three handlers + 3 tests).

#### Database/migration safety
- PASS — schema idempotent; incompatible existing schema → clean RuntimeError surfaced as sanitized 500; no shipped DB.

#### Model integrity
- PASS — sha256 recomputed 5f191bc8…b7bc1; fingerprint endpoint value == freshly computed hash (verified live).

#### Automated tests rerun
```text
53 passed in 5.33s / 53 passed in 4.49s (review)
56 passed in 4.83s (after fix-loop, orchestrator)
```

#### Frontend build rerun
```text
vite build ✓ (jspdf 341.55 kB + html2canvas 199.55 kB code-split chunks); oxlint 0 warnings 0 errors
```

#### Manual regression performed
- Reviewer live uvicorn smoke: predict → 200 with original+additive fields (source dims 180×218 for Y1.jpg), history list/detail/delete flows, 204 empty body, 404s. Orchestrator live browser verification: all three pages rendered correctly (screenshots reviewed), PDF download event fired. Cleanup: servers stopped, seeded neuroscan.db deleted.

#### Blocking findings
- none

#### Non-blocking findings
- (fixed in fix-loop) missing "History storage error." 500 detail; hardcoded StatusDot. Remaining: exportPdf starts oversized sections on a fresh page (conservative); SQLite default busy timeout without WAL (fine at scale); formatBytes duplication.

#### Decision
APPROVED WITH NON-BLOCKING NOTES (fix-loop applied; 56 tests green)

#### Required next action
- Commit phase-4; proceed to Phase 5.

## Gate Decision

**Decision:** APPROVED (with non-blocking notes; reviewer findings addressed in fix-loop)
**Phase 5 may start:** YES
**Committed as:** phase-4 commit (see Git history)

---

# Phase 5 — History Explorer & Insights

## Planner Record

### Planner Record — Phase 5

**Session ID:** PHASE-5-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** b13dd4c (phase-4 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (re-verified)

#### Binding decisions (D1–D14)
- D1–D2: stats computed in db.py via NEW read-only `scan_stats(now=None)` — ONE SQL aggregate query, never selects blob columns; injectable `now` for deterministic window tests.
- D3: rolling windows (now − 168h/720h, inclusive cutoff) via LEXICOGRAPHIC string comparison on created_at (single writer locks ISO-8601 UTC format); locked by code comment + test.
- D4–D6: 0 scans → counts 0, averages/latest NULL (never false measurements); averages rounded 2dp; count_by_prediction zero-filled for both known labels + GROUP BY overlay.
- D7: /stats failure → 500 "Stats storage error." (distinct sanitized message).
- D8–D12: explorer fully CLIENT-SIDE in HistoryList.jsx with useMemo (search over filename+prediction+id, class select, min-confidence number input, local-calendar date range via native date inputs, 4-mode sort with stable sort, clear filters, "Showing X of Y scans" count, "No scans match the selected filters." empty state). NO /history API change, no query params ever sent.
- D13–D14: nav order Analyze · History · Insights; no frontend test runner (build + lint + orchestrator browser pass).

#### /stats contract (locked)
```json
{"total_scans": int, "count_by_prediction": {"Tumour Detected": n, "No Tumour Detected": n},
 "average_confidence_percent": float|null, "average_processing_time_ms": float|null,
 "latest_scan_created_at": iso-str|null, "scans_last_7_days": int, "scans_last_30_days": int}
```

#### Wording guardrails (hard rules)
- NEVER label these accuracy/sensitivity/specificity/prevalence/F1/diagnostic performance/AUC/ECE; distribution section labeled exactly "Stored prediction distribution"; mandatory neutral caption on /insights: "These are application-history statistics about scans stored in this browser deployment — not model performance metrics." Grep-enforced at acceptance (docs/evaluation out of scope for the grep).

#### Files to change
- backend: db.py (+scan_stats, +timedelta import), main.py (+GET /stats, docstring), NEW tests/test_stats_api.py (7 tests → suite 63). Frontend: api.js (+fetchStats), HistoryList.jsx (explorer), NEW pages/Insights.jsx, App.jsx (+route+nav), App.css (+Phase 5 section). NO new dependencies.
- Frozen: DDL + existing db functions, /predict, existing tests, Home/ScanDetail/exportPdf, docs/evaluation, package.json deps.

#### Risks
- Lexicographic date comparison (locked by single writer + test); oxlint hooks deps on the useMemo (all deps listed); float AVG rounding robustness (test values chosen robustly).

#### Rollback
- Single revert of phase-5 commit; purely additive.

#### Acceptance criteria
1. 63 tests pass, no existing test edited; 2. build + lint clean; 3. /history response unchanged (history tests untouched and green); 4. browser pass: filters/sorts/clear/count/empty state, /insights six stats + distribution + caption + zero-scan + error states; 5. wording grep clean; 6. /stats SQL-aggregated without blob reads.

#### Planner decision
PROCEED

## Implementor Record

### Implementor Record — Phase 5

**Session ID:** PHASE-5-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** b13dd4c
**Branch:** main

#### Planner record followed
- yes; one deviation: the plan's date-window test seed 2026-08-01 was arithmetically outside the 30-day window for the pinned now (2026-09-25T12:00Z) — implementor moved the middle seed to 2026-09-01 to preserve the asserted windows {1, 2}. Reviewer verified this correction independently.

#### Files changed
- backend/app/db.py (+scan_stats single-aggregate + GROUP BY overlay), backend/app/main.py (+GET /stats, sanitized 500), NEW backend/tests/test_stats_api.py (7), frontend/src/api.js (+fetchStats), frontend/src/pages/HistoryList.jsx (client-side explorer), NEW frontend/src/pages/Insights.jsx, frontend/src/App.jsx (+route/nav), frontend/src/App.css (+Phase 5 section). No new dependencies.

#### Functional changes
- New GET /stats (application-history statistics; nulls-not-zeros for averages on empty DB); /history page gained search/class/min-confidence/date-range/sort/clear/count with ZERO API change; new /insights page with mandatory neutral caption + "Stored prediction distribution" bars + zero-scan state.

#### Tests added
- 7 (suite: 63 passed twice).

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest (twice: 63 passed)
cd frontend && npm run build && npm run lint (clean)
grep wording guardrails (zero hits)
```

#### Live browser verification (orchestrator)
- /history: filter bar (search, class, min confidence, from/to dates, sort, clear), "Showing 4 of 4 scans" with 4 seeded rows. /insights: caption + 6 stat cards (4 total, 94.20%, 1177.22 ms, 4/4 windows, latest timestamp) + distribution bars 1/3 matching /stats exactly. Cleanup: servers stopped, seeded neuroscan.db deleted.

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Deviations from plan
- The date-window test seed correction noted above.

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 5

**Session ID:** PHASE-5-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** b13dd4c (working tree, uncommitted phase files)
**Expected baseline commit:** b13dd4c

#### Diff independently inspected
- Changed set exactly as claimed; frozen set zero-diff (incl. package.json — no deps); no existing test modified.

#### Stats endpoint audit
- scan_stats: no blob column in any SELECT (grep); lexicographic-cutoff comment; zero-fill + overlay; None-preserving rounding; live TestClient verification by reviewer: empty DB exact 7-key body; seeded 2 rows → totals/counts/85.28/166.67/latest correct (recomputed round(x,2) semantics in-interpreter); blob sentinels absent from response; temp DB cleaned.

#### Explorer client-side-only proof
- Only the 3 baseline fetchJson occurrences remain in HistoryList.jsx; no query params; deleteRow byte-identical to baseline; helpers pure at module level; useMemo deps complete; exact empty-filter and count strings verified.

#### Insights wording audit
- Caption exact; section titled exactly "Stored prediction distribution"; six cards; zero-scan state; repo-wide grep for forbidden terms: zero hits.

#### Automated tests rerun
```text
63 passed in 5.09s / 63 passed in 4.92s
```

#### Frontend build rerun
```text
vite build ✓ 211ms; oxlint 0 warnings 0 errors
```

#### Model integrity
- PASS — sha256 recomputed 5f191bc8…b7bc1.

#### Blocking findings
- none

#### Non-blocking findings
- "single SQL aggregate" is one aggregate + one small GROUP BY (both metadata-only; wording nit); newest-mode sort uses negated ascending comparator (style nit); min-confidence accepts out-of-range values yielding empty results (acceptable).

#### Decision
APPROVED

#### Required next action
- Commit phase-5; proceed to Phase 6.

## Gate Decision

**Decision:** APPROVED
**Phase 6 may start:** YES
**Committed as:** phase-5 commit (see Git history)

---

# Phase 6 — Model Info, Readiness & Transparency

## Planner Record

### Planner Record — Phase 6

**Session ID:** PHASE-6-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 2a75656 (phase-5 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (re-verified; matches EVAL-001 fingerprint)

#### Binding decisions
- get_model_info(fingerprint) pure builder in model_info.py; backend owns its XAI {key,label} list (comment pointing at frontend source); NO paths, NO version strings, NO performance numbers.
- PROVENANCE CORRECTION: training block = {intended_dataset: "BraTS 2021 FLAIR MRI slices (train_real.py)", evaluation: "See docs/evaluation/EVALUATION_REPORT.md (EVAL-001)"} — never implies the shipped checkpoint was evaluated on BraTS (EVAL-001 evaluated the bundled Kaggle dataset).
- /ready semantics: ready iff model file present AND model_loaded (deployment-integrity probe; documented tension with /predict's model_loaded-only check is intended); SHAP background excluded; 200 body {status, model_file_present, model_loaded, device, model_fingerprint}; 503 body {status, model_file_present, model_loaded, detail:"Model assets unavailable."} (no fingerprint). /health untouched.
- Frontend: minimal — topbar MODEL readout fetches /model-info once on mount (model_name value + fingerprint tooltip; static fallback on error). No CSS/route changes.

#### Files to change
- model_info.py (+get_model_info +_XAI_METHODS), main.py (+2 routes, docstring), NEW tests/test_model_info_readiness.py (8 tests → 71), frontend/src/App.jsx (MODEL readout). Frozen: everything else.

#### Test plan
- Exact schema test; metadata values test; fingerprint==streamed sha256 test; no-path-leakage test (no backslashes, no drive letters, no MODEL_PATH value); no-performance-claims test; /ready 200 default; 503 when model_loaded=False (exact 503 body keys); 503 AND-semantics when file missing.

#### Risks
- Provenance wording (mitigated by two-key block); ready-vs-predict tension (documented); one-time fingerprint hash cost (cached); frontend fetch failure (static fallback).

#### Rollback
- Single revert; purely additive.

#### Acceptance criteria
1. 71 tests pass, existing 63 untouched; 2. /model-info exact schema incl. fingerprint==checkpoint sha; 3. /ready 200 default / 503 monkeypatched, sanitized; 4. build+lint clean; browser: MODEL readout shows BrainTumorCNN + fingerprint tooltip; 5. no paths/version claims/performance numbers in either endpoint.

#### Planner decision
PROCEED

## Implementor Record

### Implementor Record — Phase 6

**Session ID:** PHASE-6-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 2a75656
**Branch:** main

#### Planner record followed
- yes; no deviations.

#### Files changed
- backend/app/model_info.py (+_XAI_METHODS +get_model_info, docstring), backend/app/main.py (+GET /model-info, +GET /ready, docstring), NEW backend/tests/test_model_info_readiness.py (8), frontend/src/App.jsx (+ModelReadout).

#### Tests added
- 8 (suite: 71 passed twice). No existing test modified.

#### Commands executed
```text
cd backend && ./venv/Scripts/python.exe -m pytest (twice: 71 passed)
cd frontend && npm run build && npm run lint (clean)
live smoke: /health unchanged, /model-info 200 (fingerprint == streamed sha256), /ready 200 ready
```

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 6

**Session ID:** PHASE-6-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** 2a75656 (working tree, uncommitted phase files)
**Expected baseline commit:** 2a75656

#### Diff independently inspected
- Changed set exactly as claimed; frozen files zero-diff; no existing test modified.

#### model-info / ready audits
- 12-key exact schema; classes match main.py label code exactly; training block uses intended_dataset + evaluation pointer (no BraTS-evaluation claim); no paths/version claims/performance numbers (live raw-body checks incl. drive-letter regex and "%" absence). /ready: file-present AND model_loaded; 503 body without device/fingerprint; sanitized detail; frozen handlers untouched.

#### Automated tests rerun
```text
71 passed in 5.02s / 71 passed in 5.84s
```

#### Frontend build rerun
```text
vite build ✓ 178ms; oxlint 0 warnings 0 errors
```

#### Live verification
- /model-info 200 (fingerprint == reviewer's own streamed sha256); /ready 200 ready; /health unchanged. 503 path covered by monkeypatched tests.

#### Model integrity
- PASS — 5f191bc8…b7bc1 (two independent methods).

#### Blocking findings
- none

#### Non-blocking findings
- Informational: 503 body exposes condition booleans (path-free, ops-useful, intended); /ready vs /predict gate tension documented; _XAI_METHODS frontend duplication by design with pointer comment.

#### Decision
APPROVED

#### Required next action
- Commit phase-6; proceed to Phase 7.

## Gate Decision

**Decision:** APPROVED
**Phase 7 may start:** YES
**Committed as:** phase-6 commit (see Git history)

---

# Phase 7 — Final Testing, CI & Documentation

## Planner Record

### Planner Record — Phase 7

**Session ID:** PHASE-7-PLANNER (orchestrator-dispatched independent subagent)
**Date:** 2026-09-25
**Starting commit:** 435342f (phase-6 commit)
**Branch:** main
**Model SHA-256:** 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (re-verified)

#### Scope decisions
- CI: NEW .github/workflows/ci.yml ONLY (no templates/dependabot/coverage). Two parallel ubuntu jobs: backend (py3.10, CPU-index torch preinstall, pip cache, FULL pytest incl. slow) + frontend (node 22, npm ci, build, lint). Triggers: push main + PR + workflow_dispatch. No secrets.
- README surgical rewrite: regenerate stale structure tree (actual tracked tree, 71 tests); add 8-endpoint API table; add Running-the-tests section; add Model Evaluation section quoting ONLY accuracy 0.6126 + balanced accuracy 0.6370 WITH the mandatory domain-shift + non-clinical caveat and pointer to docs/evaluation/EVALUATION_REPORT.md; update highlights bullets (history/explorer/report+PDF/insights/evaluation); Quick Start ordering + neuroscan.db note. Keep badges, data-assets note, Tech Stack, BraTS, Future Work, License.
- Final verification protocol (implementor): tree clean; model sha; pytest ×2 (71); npm ci+build+lint; live endpoint loop (health→ready→model-info→predict→history→detail→delete→stats→validation errors) with temp SCAN_DB_PATH; evaluation repro into evaluation_output/repro_phase7 with timestamp-free artifacts byte-compared to docs/evaluation/ (mismatch = BLOCK).
- NOT doing: pytest-cov, frontend test runner, new features, dependency edits.

#### Files to change
- .github/workflows/ci.yml (new), README.md (edits). Ledger finalization is orchestrator-only.

#### Risks
- httpx2 on CI (verified importable from PyPI); ubuntu torch install (CPU-index preinstall + requirements fallback); README overclaim (numbers only in Model Evaluation with caveat); eval repro mismatch (same venv as EVAL-001 — investigate, never paper over).

#### Rollback
- Single revert of phase-7 commit; no data/schema/API mutations.

#### Acceptance criteria
1. ci.yml valid, two jobs, specified triggers, no secrets; 2. README matches final tree + 8-endpoint table + tests + evaluation section with caveat, no stale claims; 3. verification protocol all green and recorded; 4. nothing outside README + ci.yml modified (ledger excepted, orchestrator).

#### Planner decision
PROCEED

## Implementor Record

### Implementor Record — Phase 7

**Session ID:** PHASE-7-IMPLEMENTOR (orchestrator-dispatched independent subagent)
**Starting commit:** 435342f
**Branch:** main

#### Planner record followed
- yes; no deviations beyond YAML formatting latitude. Operational note: `npm ci` initially hit EPERM on a rolldown native binding held by four stale Vite dev-server processes from earlier live-verification sessions; they were stopped and verification ran clean.

#### Files changed
- NEW .github/workflows/ci.yml (two jobs: backend py3.10 CPU-torch + full pytest; frontend node 22 npm ci/build/lint; push-main/PR/dispatch; no secrets). README.md (surgical: highlights, regenerated structure tree, 8-endpoint API table, Running-the-tests, Model Evaluation with caveat, Quick Start notes).

#### Tests added
- None (final phase; suite validated instead: 71 passed twice).

#### Commands executed
```text
pytest ×2 (71 passed: 4.83s / 5.45s); npm ci + build + lint (clean)
live endpoint loop with temp SCAN_DB_PATH: 18/18 PASS
evaluation repro → evaluation_output/repro_phase7: 7 timestamp-free artifacts byte-identical
  to docs/evaluation/; metrics/run_metadata identical modulo timestamps; repro dir deleted
sha256(model_weights.pt) verified
```

#### Model SHA-256 after implementation
- 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1 (unchanged)

#### Deviations from plan
- none

#### Implementor status
READY FOR REVIEW

## Independent Reviewer Record

### Independent Reviewer Record — Phase 7

**Session ID:** PHASE-7-REVIEWER (orchestrator-dispatched independent subagent)
**Reviewed commit:** 435342f (working tree, uncommitted phase files)
**Expected baseline commit:** 435342f

#### Diff independently inspected
- Changed set exactly {ci.yml(new), README.md} + ledger; zero diff under backend/, frontend/, docs/.

#### CI workflow audit
- Valid YAML; two jobs with correct working directories (pytest picks up backend/pytest.ini); full suite (no slow-skip); CPU-torch preinstall sensible; triggers/permissions as specified; no secrets. Latent-risk assessment: httpx2 available on PyPI (verified live), CPU torch wheels satisfy requirements, node 22 satisfies vite 8 engines, lockfile npm ci verified locally. Residual (non-blocking): unpinned pip deps; workflow activates only once pushed to GitHub.

#### README audit
- Structure tree cross-checked against git ls-files (no phantom files); API table = the 8 real routes verified against main.py; tests section (71) correct; Model Evaluation quotes ONLY accuracy 0.6126 + balanced accuracy 0.6370, cross-checked against docs/evaluation/metrics.json rounding, with mandatory domain-shift + non-clinical caveat and report pointer; no stale claims; kept sections intact.

#### Automated tests rerun
```text
71 passed in 3.81s / 71 passed in 4.49s
```

#### Frontend build rerun
```text
vite build ✓ 337ms; oxlint 0 warnings 0 errors
```

#### Live smoke performed
- 7/7 PASS: /health, /ready, /model-info (12 keys, no paths), predict→id, history row, DELETE 204, /stats total 0 (temp DB, cleaned up).

#### Eval repro spot-check (reviewer's own run)
- predictions.csv sha256 4bb0d336…95fecf and confusion_matrix.json ecb0400b…100b406f byte-identical to docs/evaluation/; other data artifacts also identical; timestamps/commit fields the only diffs. Temp output deleted.

#### Model integrity
- PASS — 5f191bc8…b7bc1.

#### Blocking findings
- none

#### Non-blocking findings
- ci.yml untracked until commit (expected); README tree omits minor files stylistically; CI hardening ideas (pip pinning, action SHAs) deferred.

#### Decision
APPROVED WITH NON-BLOCKING NOTES

#### Required next action
- Commit phase-7; finalize Final Integrity Record + Final Sign-Off (orchestrator). Pushing to the remote is the user's call (CI activates on push).

## Gate Decision

**Decision:** APPROVED (with non-blocking notes)
**Final sign-off allowed:** YES

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

Completed 2026-09-25 after Phase 7 review (independently verified evidence in the Phase 7 records).

```text
Baseline model SHA-256: 5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1
Final model SHA-256:    5f191bc80ec9d558bccbbbf10824e1a020c1450d3a037d68a75d12b475ab7bc1
Hashes match: YES (verified by implementor, independent reviewer, and results reviewer)

Original API endpoints preserved:
  GET  /health   — unchanged (liveness, {status, model_loaded, device})
  POST /predict  — original 7 response fields byte-identical in semantics
                   (prediction, raw_probability, confidence, original_image,
                   gradcam, lrp, shap); additive fields only (id, created_at,
                   filename, content_type, size_bytes, source_dimensions,
                   processing_time_ms, model_name, model_fingerprint); DB
                   failure degrades to the original 7-field payload (200)
Original response fields preserved: YES (pinned by exact-value/superset tests)
Old Scan records readable: N/A — no history store existed at baseline (CORRECTION C-001);
  records created by Phase 4+ read back correctly (round-trip tests)

Phase 3A evaluation framework: COMPLETE + APPROVED (backend/evaluation/, 12 artifacts,
  known-value metric tests with independent re-derivation)
Phase 3B dataset: bundled Kaggle brain_tumor_dataset @ 4d0f5ed — APPROVED WITH DISCLOSURES
  2026-09-25 (manifest sha256 ca502c2b8443b0d6d854578cf085caf02e54a2fffb9db02885abc6a17e343335)
Phase 3B result status: EVAL-001 GENERATED, REPRODUCED, AND REVIEWED (accuracy 0.6126,
  balanced accuracy 0.6370 — with MANDATORY domain-shift and non-clinical caveats;
  NOT clinically meaningful; Phase 3A smoke figures superseded)

Backend tests: 71 passing (run twice at final gate; suite grew 0 → 71 across phases 0–6)
Frontend build: vite 8 build clean; oxlint 0 warnings 0 errors
Manual regression: live endpoint loop 18/18 (health→ready→model-info→predict→history→
  detail→delete→stats→validation errors); browser-verified UI (home/history/report/
  explorer/insights, PDF download event); evaluation CLI reproduced byte-identically
CI: .github/workflows/ci.yml added (backend pytest incl. slow + frontend build/lint;
  activates on push — push is the user's decision)
```

The Phase 3B pending-dataset statement is NOT required: an approved dataset was processed and
independently reviewed. All numerical claims live in docs/evaluation/ and EVAL-001 with their
caveats; the frontend carries no performance claims (grep-enforced).

---

## Final Sign-Off

**Status:** SIGNED OFF — 2026-09-25

All mandatory phase gates approved:
- Phase 0 APPROVED WITH NON-BLOCKING NOTES (2996163)
- Phase 1 APPROVED WITH NON-BLOCKING NOTES (1f72ab7)
- Phase 2 APPROVED (dbf4aea)
- Phase 3A APPROVED (58de4ed) — FRAMEWORK: APPROVED
- Phase 3B APPROVED WITH NON-BLOCKING NOTES (adbc019) — EVAL-001 generated, reproduced, reviewed
- Phase 4 APPROVED WITH NON-BLOCKING NOTES (b13dd4c; reviewer findings fixed in-loop)
- Phase 5 APPROVED (2a75656)
- Phase 6 APPROVED (435342f)
- Phase 7 APPROVED WITH NON-BLOCKING NOTES (final commit)

Final state: the frozen compatibility contract holds (FastAPI + React/Vite + PyTorch BrainTumorCNN,
frozen checkpoint, binary semantics, Grad-CAM/LRP/SHAP, preprocessing contract, original endpoints
and fields preserved); all improvements are additive and independently reviewed; the checkpoint is
byte-identical to baseline; evaluation results are traceable to a committed dataset manifest, exact
commands, and reproducible artifacts.

Known accepted limitations (documented, non-blocking): single-process deployment assumptions
(SQLite, event-loop serialization of XAI), unpinned CI pip installs, LICENSE copyright holder
placeholder ("NeuroScan XAI Authors"), duplicate dataset copy retained by user decision, EVAL-001
domain-shift caveat on all performance figures.

Local commits only — pushing to the origin remote (which activates CI) is left to the repository owner.
