# Quick Start Guide

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

Sau khi deploy, sẽ nhận được URL như:
```
https://your-username--glm-ocr-api-ocr-endpoint.modal.run
```

**Lưu URL này lại**

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

Backend chạy tại: http://localhost:8000
API Docs: http://localhost:8000/api/docs

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

Frontend chạy tại: http://localhost:3000

