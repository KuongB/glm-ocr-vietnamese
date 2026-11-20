# Annotation Pipeline

A multi-stage annotation pipeline for building a Vietnamese handwriting
image–text dataset. Raw images go in, reviewed image–text pairs come out.

```
                 ┌──────────────┐
  images/  ─────▶│   1. OCR     │  semi-automatic draft transcription
                 │  (GLM-OCR)   │  → draft_text
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  2. SLM      │  spelling / diacritic correction
                 │  correction  │  → corrected_text
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  3. Manual   │  human accepts or edits the text
                 │    review    │  → final_text
                 └──────┬───────┘
                        ▼
              dataset.jsonl + label.json
```

Both models sit behind HTTP endpoints, so this package has **no ML
dependencies** — no torch, no transformers. It is an orchestration layer: it
sends images and text to endpoints, tracks state, and puts a human in front of
the result.

---

## Why it is shaped this way

**Everything is resumable.** Each image is one record in a JSONL manifest with a
status. A stage only picks up records sitting in the status it expects, so
re-running any command after a crash, a timeout, or a laptop lid closing costs
nothing and repeats nothing. Progress is flushed to disk as the run proceeds,
not at the end.

**Failures are data, not exceptions.** A record whose OCR call fails lands in
`ocr_failed` with the error recorded on it, and the run continues. The next run
retries exactly those records.

**The human is the last word.** Stages 1 and 2 only produce a *suggestion*.
Nothing enters the exported dataset until a person has approved it, and what
they approve is whatever text is in the edit box, not what the model said.

---

## Record lifecycle

```
pending ──stage 1──▶ drafted ──stage 2──▶ corrected ──stage 3──▶ approved
   │                    │                     │                      │
   └──▶ ocr_failed      └──▶ correct_failed   └──stage 3──▶ rejected ┘
          (retried)            (retried)
```

`approved` and `rejected` are terminal. Records in `drafted` are reviewable too,
so stage 2 can be skipped entirely if you only want raw OCR plus human review.

---

## Setup

```bash
cd annotation_pipeline
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/macOS

pip install -r requirements.txt

copy .env.example .env         # Windows
cp .env.example .env           # Linux/macOS
```

Edit `.env` and set the two endpoint URLs:

```env
OCR_API_URL=https://<you>--glm-ocr-api-ocr-endpoint.modal.run
CORRECTOR_API_URL=https://<you>--vn-spell-correction-api-correct-endpoint.modal.run
```

Then drop the images to annotate into `data/images/` (subfolders are fine and
are preserved in the output).

---

## Running it

```bash
python run_pipeline.py scan       # register images as pending records
python run_pipeline.py ocr        # stage 1: draft transcriptions
python run_pipeline.py correct    # stage 2: SLM spelling correction
python run_pipeline.py review     # stage 3: opens the review UI
python run_pipeline.py export     # write approved pairs out
```

`auto` runs the three automated steps in one go and stops before the human
stage:

```bash
python run_pipeline.py auto
python run_pipeline.py status     # status counts at any time
```

Every command is safe to re-run. `--limit N` caps how many records a stage
processes, which is useful for a first smoke test against a live endpoint:

```bash
python run_pipeline.py ocr --limit 5
```

---

## Stage 1 — semi-automatic OCR

Sends each image to the GLM-OCR endpoint (`../serve.py`) and stores the result
as `draft_text`. Requests run concurrently (`CONCURRENCY`, default 4) with
retry and exponential back-off, because the endpoint is serverless and the
first call after an idle period cold-starts for 20–30s.

The draft is explicitly *not* trusted. Its job is to turn review from
"transcribe this from scratch" into "fix what is wrong", which is where the
throughput gain comes from.

## Stage 2 — SLM correction

Batches the drafts (`CORRECTOR_BATCH_SIZE`, default 16) and POSTs them to the
correction endpoint, storing the result as `corrected_text`. The model is
[`nrl-ai/vn-spell-correction-small`](https://huggingface.co/nrl-ai/vn-spell-correction-small),
a BARTpho-based seq2seq model that restores diacritics and fixes spelling —
exactly the errors OCR makes most on Vietnamese handwriting.

The pipeline only sends text and reads text back. The model id is recorded on
each record so you can tell later which model produced which correction.

**Request / response contract:**

```jsonc
// POST
{ "texts": ["toi di hoc", "ha noi"] }
// 200
{ "corrected": ["tôi đi học", "hà nội"] }
```

The client also accepts `{"texts": [...]}`, `{"results": [...]}`,
`{"outputs": [...]}` or a bare JSON array, so the endpoint can be re-hosted
behind a different serving stack without touching the pipeline.

### Hosting the corrector

`serve_corrector.py` deploys that model to Modal and implements the contract
above:

```bash
modal secret create huggingface-token HF_TOKEN=<your-token>   # once
modal deploy serve_corrector.py
```

It runs on an L4 (the correction model is far smaller than the OCR model) and
caches weights in a Modal volume so cold starts stay short. Put the printed URL
in `CORRECTOR_API_URL`. If you already host this model elsewhere, skip this file
entirely and just point the URL at your endpoint.

## Stage 3 — manual review

```bash
python run_pipeline.py review --reviewer your-name
```

Opens a local review UI on `http://127.0.0.1:8100`:

- the image beside the OCR draft and the SLM-corrected text
- an editable **Final text** box, pre-filled with the corrected text
- a badge saying whether the SLM actually changed the draft, so unchanged
  records can be skimmed faster
- **Approve** (`Ctrl+Enter`), **Reject** (`Ctrl+Del`), **Skip** (`Ctrl+→`)
- an optional note, kept on rejected records so you can see *why* later

Each decision is written to the manifest immediately — closing the browser
mid-session loses nothing. Approve stores whatever is in the edit box. Reject
marks the image unusable and keeps it out of the export.

The server is built for one reviewer at a time against one manifest. For
several reviewers in parallel, split the images into separate folders with their
own manifests and run one server per reviewer.

---

## Output

```bash
python run_pipeline.py export
```

Writes to `data/export/` (only `approved` records):

| File | Shape |
|---|---|
| `dataset.jsonl` | `{"image": "sub/1.jpg", "text": "...", "id": "..."}` per line |
| `label.json` | `{"sub/1.jpg": "..."}` — the format used elsewhere in this repo |

`label.json` is keyed by path relative to `IMAGES_DIR`, not by basename, so two
images called `1.jpg` in different subfolders do not collide.

---

## Configuration

All settings come from `.env` or the environment.

| Variable | Default | Meaning |
|---|---|---|
| `OCR_API_URL` | *(required for `ocr`)* | GLM-OCR endpoint |
| `OCR_API_TOKEN` | — | Bearer token, if the endpoint needs one |
| `CORRECTOR_API_URL` | *(required for `correct`)* | Correction endpoint |
| `CORRECTOR_API_TOKEN` | — | Bearer token, if needed |
| `CORRECTOR_BATCH_SIZE` | `16` | Texts per correction request |
| `REQUEST_TIMEOUT` | `120` | Per-request timeout (seconds) |
| `MAX_RETRIES` | `3` | Attempts before a record is marked failed |
| `CONCURRENCY` | `4` | Concurrent in-flight requests per stage |
| `IMAGES_DIR` | `data/images` | Images to annotate |
| `MANIFEST_PATH` | `data/manifest.jsonl` | Record store |
| `EXPORT_DIR` | `data/export` | Export destination |
| `REVIEW_HOST` / `REVIEW_PORT` | `127.0.0.1` / `8100` | Review server bind |
| `REVIEWER_NAME` | `reviewer` | Recorded on each decision |

Retries fire on timeouts, network errors and 5xx. A 4xx fails immediately —
a bad payload or bad token will not fix itself on a retry.

---

## Layout

```
annotation_pipeline/
├── run_pipeline.py              # CLI: scan / ocr / correct / review / export / status / auto
├── serve_corrector.py           # Modal deployment for the correction SLM
├── pipeline/
│   ├── config.py                # settings (pydantic-settings)
│   ├── schema.py                # Record, RecordStatus, stage transitions
│   ├── store.py                 # JSONL manifest, atomic writes, queries
│   ├── clients.py               # OCR + corrector HTTP clients, retry policy
│   ├── export.py                # dataset.jsonl + label.json
│   ├── stages/
│   │   ├── ocr_draft.py         # stage 1
│   │   └── correct.py           # stage 2
│   └── review/
│       ├── app.py               # stage 3: FastAPI review server
│       └── static/index.html    # review UI
├── tests/                       # 78 tests, no network access
└── data/                        # images, manifest, exports (gitignored)
```

---

## Tests

```bash
python -m pytest
```

78 tests covering the store and its atomic writes, the retry policy, response
parsing, both stages against a mock transport (success, failure, resume,
batching), the review API including a path-traversal check, and the CLI. All
HTTP is mocked, so the suite needs no endpoints and no network.
