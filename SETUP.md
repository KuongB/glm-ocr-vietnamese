# Quick Setup Guide - OCR Service

## Cài đặt nhanh

### Bước 1: Cài đặt Backend

```bash
# Di chuyển vào thư mục backend
cd backend

# Tạo môi trường ảo Python
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Tạo file cấu hình
copy .env.example .env
# Chỉnh sửa file .env nếu cần

# Chạy server
python main.py
```

Backend sẽ chạy tại: http://localhost:8000
API Docs: http://localhost:8000/api/docs

### Bước 2: Cài đặt Frontend

Mở terminal mới:

```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt các package
npm install

# Tạo file cấu hình
copy .env.example .env
# Đảm bảo VITE_API_URL=http://localhost:8000/api

# Chạy server phát triển
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

## Cài đặt với Docker (Khuyến nghị)

```bash
# Từ thư mục gốc của project
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down
```

Truy cập:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## Kiểm tra

1. Mở trình duyệt và truy cập http://localhost:3000
2. Tải lên một ảnh có chứa văn bản
3. Nhấn "Trích xuất văn bản"
4. Xem kết quả

## Lỗi thường gặp

### Backend không khởi động được

- Kiểm tra Python version: `python --version` (cần 3.11+)
- Kiểm tra đã cài đặt dependencies: `pip list`
- Xem chi tiết lỗi trong terminal

### Frontend không kết nối được với Backend

- Đảm bảo Backend đang chạy
- Kiểm tra file `.env` trong frontend
- Xem console trong trình duyệt (F12)

### Port bị chiếm dụng

- Backend (8000): Thay đổi port trong `backend/main.py`
- Frontend (3000): Thay đổi port trong `frontend/vite.config.js`

## Tiếp theo

- Đọc [README.md](README.md) để hiểu thêm về architecture
- Đọc [backend/README.md](backend/README.md) để tìm hiểu về API
- Đọc [frontend/README.md](frontend/README.md) để tìm hiểu về UI

## Support

Nếu gặp vấn đề, hãy:
1. Kiểm tra logs trong terminal
2. Xem API docs tại http://localhost:8000/api/docs
3. Tạo issue trên GitHub repository
