# Deploy Modal OCR Endpoint - Hướng dẫn

## Bước 1: Cài đặt Modal

```bash
pip install modal
```

## Bước 2: Đăng ký và đăng nhập Modal

```bash
# Tạo tài khoản tại https://modal.com
modal setup
```

## Bước 3: Tạo HuggingFace Token Secret

```bash
modal secret create huggingface-token HF_TOKEN=your_huggingface_token_here
```

Lấy HuggingFace token tại: https://huggingface.co/settings/tokens

## Bước 4: Deploy Model lên Modal

```bash
# Từ thư mục gốc của project
modal deploy serve.py
```

Sau khi deploy thành công, bạn sẽ nhận được URL endpoint dạng:
```
https://your-username--glm-ocr-api-ocr-endpoint.modal.run
```

## Bước 5: Cấu hình Backend

Mở file `backend/.env` và cập nhật:

```env
USE_LOCAL_MODEL=False
MODAL_API_URL=https://your-username--glm-ocr-api-ocr-endpoint.modal.run
MODAL_TIMEOUT=60
MODAL_MAX_RETRIES=3
```

## Bước 6: Test Modal Endpoint

```bash
# Từ thư mục gốc
python test-modal-endpoint.py path/to/image.jpg
```

## Lưu ý quan trọng

### Cold Start
- Lần đầu tiên gọi API sau khi deploy hoặc sau thời gian idle, model sẽ mất ~20-30s để khởi động (cold start)
- Backend đã được cấu hình retry logic để xử lý cold start tự động
- Các request tiếp theo sẽ nhanh hơn (~2-5s)

### Chi phí
- Modal miễn phí $30/tháng credit
- GPU T4: ~$0.60/hour
- Model tự động shutdown sau 5 phút idle để tiết kiệm chi phí

### Monitoring
Xem logs và metrics tại: https://modal.com/apps

## Troubleshooting

### Lỗi: "Secret not found"
```bash
modal secret list
modal secret create huggingface-token HF_TOKEN=your_token
```

### Lỗi: "Model not found"
Kiểm tra `HF_REPO_ID` trong serve.py có đúng không

### Lỗi: "GPU quota exceeded"
Upgrade Modal plan hoặc đợi reset quota

## Development vs Production

### Development (serve local)
```bash
modal serve serve.py
# URL: http://localhost:8000/ocr_endpoint
```

### Production (deploy)
```bash
modal deploy serve.py
# URL: https://your-username--glm-ocr-api-ocr-endpoint.modal.run
```

## Cập nhật Model

Sau khi thay đổi serve.py:

```bash
modal deploy serve.py
```

Model deployment sẽ được cập nhật mà không cần downtime.
