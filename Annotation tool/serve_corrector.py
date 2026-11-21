"""Host the Vietnamese spelling-correction SLM on Modal.

This is the endpoint stage 2 of the pipeline talks to. Deploy it once and put
the URL in ``CORRECTOR_API_URL``; the pipeline itself never loads the model.

    modal secret create huggingface-token HF_TOKEN=<your-token>   # once
    modal deploy serve_corrector.py

    # ad-hoc check
    curl -X POST <url> -H 'Content-Type: application/json' \
         --data '{"texts": ["toi di hoc"]}'

The model is ``nrl-ai/vn-spell-correction-small``, a BARTpho-based seq2seq
model, so correction is plain conditional generation. It runs comfortably on an
L4; it is far smaller than the OCR model and does not need an H100.

Contract (what ``pipeline/clients.py`` expects):

    request   {"texts": ["...", "..."]}   or   {"text": "..."}
    response  {"corrected": ["...", "..."], "model": "...", "count": N}
"""

from __future__ import annotations

import modal

MODEL_ID = "nrl-ai/vn-spell-correction-small"

#: Longest input (in tokens) sent to the model; longer text is split on
#: sentence boundaries by the caller if needed.
MAX_INPUT_TOKENS = 256
MAX_OUTPUT_TOKENS = 320

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        [
            "torch",
            "transformers",
            "sentencepiece",
            "huggingface_hub",
            "fastapi[standard]",
        ]
    )
)

app = modal.App("vn-spell-correction-api", image=image)

#: Cache the weights in a volume so a cold start does not re-download them.
model_cache = modal.Volume.from_name("vn-spell-correction-cache", create_if_missing=True)
CACHE_DIR = "/cache"


@app.cls(
    gpu="L4",
    volumes={CACHE_DIR: model_cache},
    secrets=[modal.Secret.from_name("huggingface-token")],
    scaledown_window=300,
)
class SpellCorrector:
    """BARTpho-based Vietnamese spelling corrector."""

    @modal.enter()
    def load_model(self):
        import os

        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        os.environ.setdefault("HF_HOME", CACHE_DIR)
        token = os.environ.get("HF_TOKEN")

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID, cache_dir=CACHE_DIR, token=token
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_ID, cache_dir=CACHE_DIR, token=token
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()
        print("Loaded %s on %s" % (MODEL_ID, self.device))

    @modal.method()
    def correct(self, texts: list[str]) -> list[str]:
        """Correct a batch of texts, returning one output per input.

        Empty and whitespace-only inputs are passed through untouched rather
        than sent to the model, which would hallucinate text for them.
        """
        torch = self.torch

        # Remember which inputs are worth running so the output lines up 1:1.
        indexed = [(i, t) for i, t in enumerate(texts) if (t or "").strip()]
        out: list[str] = list(texts)
        if not indexed:
            return out

        batch = [t for _, t in indexed]
        encoded = self.tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
        ).to(self.device)

        with torch.no_grad():
            generated = self.model.generate(
                **encoded,
                max_length=MAX_OUTPUT_TOKENS,
                num_beams=4,
                early_stopping=True,
            )

        decoded = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
        for (position, _), corrected in zip(indexed, decoded):
            out[position] = corrected.strip()
        return out


corrector = SpellCorrector()


@app.function()
@modal.fastapi_endpoint(method="POST")
def correct_endpoint(item: dict) -> dict:
    """POST {"texts": [...]} (or {"text": "..."}) -> {"corrected": [...]}."""
    if "texts" in item:
        texts = item["texts"]
        if not isinstance(texts, list):
            return {"error": "'texts' must be a list of strings"}
    elif "text" in item:
        texts = [item["text"]]
    else:
        return {"error": "send either 'texts' (list) or 'text' (string)"}

    texts = ["" if t is None else str(t) for t in texts]
    corrected = corrector.correct.remote(texts)
    return {"corrected": corrected, "model": MODEL_ID, "count": len(corrected)}
