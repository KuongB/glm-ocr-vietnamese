import requests, base64

# Đổi thành ảnh test của bạn
with open("giotsuatraoem.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = requests.post(
    "https://kuongb--glm-ocr-api-ocr-endpoint-dev.modal.run",  # ← URL từ terminal modal serve
    json={"image_b64": b64}
)

print(response.status_code)
print(response.json())