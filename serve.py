import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "torch", "torchvision", "transformers", "peft",
        "Pillow", "accelerate", "einops",
        "sentencepiece", "huggingface_hub",
        "fastapi[standard]"       
    ])
)

app = modal.App("glm-ocr-api", image=image)

HF_REPO_ID = "KuongB/glm-ocr-vietnamese"

@app.cls(gpu="T4", secrets=[modal.Secret.from_name("huggingface-token")])
class GLMOCRModel:

    @modal.enter()
    def load_model(self):
        import os, torch, importlib
        from transformers import AutoProcessor, AutoConfig
        from huggingface_hub import snapshot_download

        token = os.environ["HF_TOKEN"]
        model_path = snapshot_download(HF_REPO_ID, token=token)

        # Tìm đúng class ForConditionalGeneration của GLM-OCR
        cfg = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
        module = importlib.import_module(
            f"transformers.models.{cfg.model_type.replace('-', '_')}"
        )
        gen_cls = next(
            getattr(module, a) for a in dir(module)
            if "ForConditionalGeneration" in a
        )

        self.processor = AutoProcessor.from_pretrained(
            model_path, trust_remote_code=True
        )
        self.model = gen_cls.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        self.model.eval()
        print("Model loaded!")

    @modal.method()
    def predict(self, image_bytes: bytes) -> str:
        import torch
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text",  "text": "Text Recognition:"}
            ]
        }]
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=[text], images=[image], return_tensors="pt"
        ).to("cuda")

        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=256, do_sample=False
            )
        generated = out[0][inputs["input_ids"].shape[1]:]
        return self.processor.tokenizer.decode(
            generated, skip_special_tokens=True
        ).strip()


@app.function()
@modal.fastapi_endpoint(method="POST")
def ocr_endpoint(item: dict) -> dict:
    import base64
    image_bytes = base64.b64decode(item["image_b64"])
    result = GLMOCRModel().predict.remote(image_bytes)
    return {"text": result}