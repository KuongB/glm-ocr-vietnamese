# Vietnamese Handwritten OCR

Recognising handwritten Vietnamese text from images, end to end: building the labelled
dataset, benchmarking OCR engines, fine-tuning a vision–language model, and serving it
through a web application.

**Course project** — CSC14005 Introduction to Machine Learning, Class 23KHDL1, Group 6.
Fine-tuned model: [KuongB/glm-ocr-vietnamese](https://huggingface.co/KuongB/glm-ocr-vietnamese)

---

## Repository layout

| Folder / file | What it is |
|---|---|
| **`Main repo/`** | The machine-learning work. Notebooks for data cleaning, EDA and stratified splitting; baseline evaluation of Tesseract 5.x, PaddleOCR and GLM-OCR; LoRA fine-tuning of GLM-OCR. Includes the per-model result CSVs and the proposal / data reports under `docs/`. |
| **`Application repo/`** | The web application. React + Vite frontend, FastAPI backend acting as a proxy, and `serve.py` which deploys the model to Modal serverless GPU. Docker Compose runs both services. |
| **`Annotation tool/`** | Tooling used to *build* the labelled corpus. A three-stage pipeline — OCR draft, small-language-model spelling correction, then human review in a local web UI — that turns raw images into reviewed image–text pairs. |
| **`Report.pdf`** | Final course report, Vietnamese, 49 pages. The complete write-up. |
| **`Slide.pdf`** | Presentation deck, 30 slides. |
| **`Annotation_and_Finetuning_Report.pdf`** | Supplementary technical report, English, 4 pages, covering the annotation tool and the fine-tuning setup. |
| **`Model.txt`** | Link to the published model. |

---

## How the pieces fit together

```
  raw handwriting images
          │
          ▼
  ┌─────────────────┐     labelled pairs      ┌──────────────┐
  │ Annotation tool │ ──────────────────────▶ │  Main repo   │  fine-tune GLM-OCR
  └─────────────────┘                         └──────┬───────┘
                                                     │ merged model → HuggingFace
                                                     ▼
                                           ┌───────────────────┐
                                           │ Application repo  │  Modal + FastAPI + React
                                           └───────────────────┘
```

---

## Results

Baselines on the full 15,000-image test set, and GLM-OCR after LoRA fine-tuning on 1,000
samples (200-image evaluation subset). Metric is Character Error Rate — lower is better.

| Model | Average CER |
|---|---|
| Tesseract 5.x | 98.59% |
| GLM-OCR (base) | 90.40% |
| PaddleOCR | 57.29% |
| **GLM-OCR fine-tuned** | **29.72%** |

Fine-tuning cut GLM-OCR's error rate from 85.00% to 29.72% on the same subset — a 65%
relative reduction. Full method and caveats are in `Annotation_and_Finetuning_Report.pdf`.

---

## Getting started

Each folder has its own README with full instructions.

**Run the web app** — see [`Application repo/README.md`](Application%20repo/README.md).
Deploy `serve.py` to Modal first, then put the endpoint URL in `backend/.env` as
`MODAL_API_URL`; the backend is only a proxy and needs it to answer any request.

**Reproduce the ML results** — see [`Main repo/README.md`](Main%20repo/README.md).
The notebooks are written for Google Colab and mount the dataset from Google Drive.

**Annotate new data** — see [`Annotation tool/README.md`](Annotation%20tool/README.md).

```bash
cd "Annotation tool"
pip install -r requirements.txt
python run_pipeline.py auto      # OCR draft + SLM correction
python run_pipeline.py review    # human review at http://127.0.0.1:8100
python run_pipeline.py export    # dataset.jsonl + label.json
```

---

## Team

| Student ID | Name |
|---|---|
| 23127102 | Le Quang Phuc |
| 23127212 | Nguyen Quang Dang Khoa |
| 23127241 | Doan Thanh Phat |
| 23127332 | Tran Tien Cuong |
| 23127442 | Tram Huu Nhan |
