# 🚀 Quick Start Guide - OCR Service với Modal API

## Tổng quan

Website OCR này sử dụng:
- **Frontend**: React + Vite (port 3000)
- **Backend**: FastAPI (port 8000)
- **Model**: GLM-OCR trên Modal (serverless GPU)

## Bước 1: Deploy Model lên Modal 

### 1.1. Cài đặt Modal

```bash
pip install modal
```

### 1.2. Đăng ký và đăng nhập

```bash
modal setup
```

Làm theo hướng dẫn để tạo tài khoản tại https://modal.com

### 1.3. Tạo HuggingFace Token Secret

```bash
modal secret create huggingface-token HF_TOKEN=your_token_here
```

Lấy token tại: https://huggingface.co/settings/tokens

### 1.4. Deploy

```bash
# Từ thư mục gốc của project
modal deploy serve.py
```

✅ Sau khi deploy, bạn sẽ nhận được URL như:
```
https://your-username--glm-ocr-api-ocr-endpoint.modal.run
```

**Lưu URL này lại!**

## Bước 2: Cài đặt Backend

### 2.1. Tạo môi trường ảo

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2.2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2.3. Cấu hình

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Mở file `.env` và cập nhật:

```env
# Tắt local model
USE_LOCAL_MODEL=False

# Thêm Modal API URL (thay your-username bằng username Modal của bạn)
MODAL_API_URL=https://your-username--glm-ocr-api-ocr-endpoint.modal.run

# Timeout và retry
MODAL_TIMEOUT=60
MODAL_MAX_RETRIES=3
```

### 2.4. Kiểm tra cấu hình

```bash
python check_health.py
```

### 2.5. Chạy backend

```bash
python main.py
```

✅ Backend chạy tại: http://localhost:8000
📚 API Docs: http://localhost:8000/api/docs

## Bước 3: Cài đặt Frontend

Mở **terminal mới** (giữ backend đang chạy):

### 3.1. Cài đặt Node.js

Nếu chưa có Node.js, tải tại: https://nodejs.org/ (chọn LTS)

### 3.2. Cài đặt dependencies

```bash
cd frontend
npm install
```

### 3.3. Cấu hình

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

File `.env` mặc định đã đúng:
```env
VITE_API_URL=http://localhost:8000/api
```

### 3.4. Chạy frontend

```bash
npm run dev
```

✅ Frontend chạy tại: http://localhost:3000

## Bước 4: Sử dụng

1. Mở trình duyệt: http://localhost:3000
2. Kéo thả hoặc chọn một ảnh có chứa văn bản
3. Nhấn "Trích xuất văn bản"
4. Đợi 2-30 giây (lần đầu có thể lâu do cold start)
5. Xem kết quả và copy/download

## Test Modal Endpoint (Optional)

```bash
# Từ thư mục gốc
python test-modal-endpoint.py path/to/image.jpg https://your-modal-url.modal.run
```

## Lưu ý quan trọng

### Cold Start
- Lần đầu tiên gọi API sau khi deploy hoặc idle lâu, model mất ~20-30s để khởi động
- Backend có retry logic tự động xử lý
- Các request tiếp theo chỉ mất ~2-5s

### Chi phí Modal
- Miễn phí $30/month credit
- GPU T4: ~$0.60/hour
- Model tự động shutdown sau idle để tiết kiệm chi phí

### Kiểm tra logs
```bash
# Backend logs
# Xem terminal đang chạy backend

# Modal logs
modal app list
modal app logs glm-ocr-api
```

## Troubleshooting

### Backend không kết nối được Modal

**Kiểm tra:**
1. Modal URL có đúng không? (copy từ kết quả `modal deploy`)
2. Modal deployment có chạy không? (`modal app list`)
3. Xem logs backend có lỗi gì không

**Sửa:**
```bash
# Xem Modal apps
modal app list

# Xem logs Modal
modal app logs glm-ocr-api

# Re-deploy nếu cần
modal deploy serve.py
```

### Request timeout

- Lần đầu tiên có thể mất 20-30s (cold start)
- Backend tự động retry 3 lần
- Nếu vẫn lỗi, kiểm tra Modal logs

### Frontend không kết nối Backend

**Kiểm tra:**
1. Backend có đang chạy? (http://localhost:8000/api/health)
2. File `.env` trong frontend có đúng không?

**Sửa:**
```bash
# Test backend health
curl http://localhost:8000/api/health

# Hoặc mở browser
http://localhost:8000/api/docs
```

### Modal Secret not found

```bash
# Xem secrets
modal secret list

# Tạo lại
modal secret create huggingface-token HF_TOKEN=your_token
```

## Cấu trúc Hoàn chỉnh

```
User Browser (localhost:3000)
    ↓ HTTP Request
Frontend (React/Vite)
    ↓ API Call
Backend (FastAPI:8000)
    ↓ HTTP POST
Modal API (Serverless GPU)
    ↓ GLM-OCR Model
    ↑ Extracted Text
Backend
    ↑ JSON Response
Frontend
    ↑ Display Result
User
```

## Cần giúp đỡ?

1. Xem logs backend trong terminal
2. Xem API docs: http://localhost:8000/api/docs
3. Xem Modal logs: `modal app logs glm-ocr-api`
4. Xem file MODAL_DEPLOYMENT.md để biết thêm chi tiết
5. Tạo issue trên GitHub

---

**Happy OCR-ing! 🎉**
