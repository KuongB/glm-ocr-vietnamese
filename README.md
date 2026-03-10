# OCR Service - Professional Web Application

Đồ án Nhập môn học máy - HCMUS - Khóa 23CLC

A complete, production-ready OCR (Optical Character Recognition) web application with modern frontend and backend architecture.

## 🌟 Features

- **High-Quality OCR**: Vietnamese text recognition using GLM-OCR model
- **Modern UI**: Beautiful, responsive React interface
- **Fast Processing**: Optimized backend with FastAPI
- **Easy Deployment**: Docker support for both frontend and backend
- **RESTful API**: Well-documented API with Swagger/ReDoc
- **File Upload**: Drag & drop or click to upload images
- **Result Management**: Copy to clipboard or download as text file
- **Real-time Feedback**: Loading states and error handling

## 📁 Project Structure

```
IntroML-OCR/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py     # App factory
│   │   ├── config.py       # Configuration
│   │   ├── models/         # Pydantic schemas
│   │   ├── routes/         # API endpoints
│   │   └── services/       # Business logic
│   ├── main.py             # Entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── README.md
├── docker-compose.yml       # Docker orchestration
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- Modal account (for serverless GPU deployment)

### Option 1: Run with Modal API (Recommended for Production)

**Step 1: Deploy Model to Modal**

```bash
# Install Modal
pip install modal

# Setup Modal account
modal setup

# Create HuggingFace token secret
modal secret create huggingface-token HF_TOKEN=your_token

# Deploy to Modal
modal deploy serve.py
```

You'll get a URL like: `https://username--glm-ocr-api-ocr-endpoint.modal.run`

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

**Step 2: Configure and Run Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows

pip install -r requirements.txt
copy .env.example .env

# Edit .env and set:
# USE_LOCAL_MODEL=False  
# MODAL_API_URL=https://your-modal-url.modal.run

python main.py
```

**Step 3: Run Frontend**

```bash
cd frontend
npm install
npm run dev
```

Access: http://localhost:3000

### Option 2: Run with Docker Compose

```bash
# Start both frontend and backend
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Option 3: Run Manually (Local Development)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run server
python main.py
```

Backend will be available at http://localhost:8000

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with backend URL

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

## 📖 Documentation

### Quick Start

- [QUICKSTART.md](QUICKSTART.md) - Complete step-by-step guide with Modal deployment
- [MODAL_DEPLOYMENT.md](MODAL_DEPLOYMENT.md) - Detailed Modal deployment instructions
- [SETUP.md](SETUP.md) - Alternative setup without Docker

### Backend API

Full API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

#### Key Endpoints

```
POST /api/ocr/extract           - Extract text from base64 image
POST /api/ocr/upload            - Upload and extract text from file
GET  /api/ocr/supported-languages - Get supported languages
GET  /api/health                - Health check
```

See [backend/README.md](backend/README.md) for detailed backend documentation.

### Frontend

See [frontend/README.md](frontend/README.md) for detailed frontend documentation.

## 🔧 Configuration

### Backend Environment Variables

```env
# Application
APP_NAME=OCR Service API
VERSION=1.0.0
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000

# Model
HF_REPO_ID=KuongB/glm-ocr-vietnamese
MAX_IMAGE_SIZE=10485760

# Modal/Local Model
USE_LOCAL_MODEL=False
MODAL_API_URL=
```

### Frontend Environment Variables

```env
VITE_API_URL=http://localhost:8000/api
```

## 🐳 Docker Deployment

### Build Images

```bash
# Build backend
docker build -t ocr-backend ./backend

# Build frontend
docker build -t ocr-frontend ./frontend
```

### Run Containers

```bash
# Run backend
docker run -p 8000:8000 --env-file backend/.env ocr-backend

# Run frontend
docker run -p 3000:80 ocr-frontend
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Scale backend
docker-compose up -d --scale backend=3

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│  User Browser   │
│  (localhost:3000)│
└────────┬────────┘
         │ HTTP Request
         ↓
┌─────────────────┐
│  Frontend       │
│  React + Vite   │
│  Port 3000      │
└────────┬────────┘
         │ REST API
         ↓
┌─────────────────┐
│  Backend        │
│  FastAPI        │
│  Port 8000      │
└────────┬────────┘
         │ HTTP POST (base64 image)
         ↓
┌─────────────────┐
│  Modal API      │
│  Serverless GPU │
│  GLM-OCR Model  │
└─────────────────┘
```

### Backend (FastAPI)

- **Framework**: FastAPI for high performance async operations
- **Validation**: Pydantic models for request/response validation
- **CORS**: Configured for frontend access
- **Error Handling**: Retry logic with exponential backoff for Modal API
- **Logging**: Comprehensive logging for debugging
- **Documentation**: Auto-generated OpenAPI docs (Swagger/ReDoc)

**Key Features**:
- Automatic retry on timeout (cold start handling)
- Request validation and image size limits
- Base64 and file upload support
- Health check endpoints

### Frontend (React + Vite)

- **Framework**: React 18 with modern hooks
- **Build Tool**: Vite for lightning-fast development
- **Styling**: Custom CSS with CSS variables for theming
- **State Management**: React hooks (useState, useCallback, useEffect)
- **HTTP Client**: Axios with custom configuration
- **File Upload**: react-dropzone for drag & drop interface

**Key Features**:
- Real-time processing status
- Image preview before processing
- Copy to clipboard functionality
- Download results as text file
- Responsive design (mobile-friendly)

### Modal Integration

**Why Modal?**
- ✅ Serverless GPU infrastructure (no server management)
- ✅ Auto-scaling and automatic shutdown when idle
- ✅ Pay only for actual usage (~$0.60/hour for T4 GPU)
- ✅ Cold start handled by backend retry logic
- ✅ $30 free credit per month

**Flow**:
1. Frontend sends image to Backend
2. Backend validates and encodes image to base64
3. Backend calls Modal API endpoint
4. Modal loads model (cold start: 20-30s first time)
5. Model processes image and extracts text
6. Result returns through Backend to Frontend

### Communication Flow

```
1. User uploads image → Frontend
2. Frontend converts to base64 → POST /api/ocr/extract
3. Backend validates image → Calls Modal API
4. Modal API processes with GLM-OCR → Returns text
5. Backend returns result → Frontend displays
6. User can copy/download result
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 📝 Usage Example

### Using the Web Interface

1. Open http://localhost:3000
2. Drag & drop an image or click to upload
3. Click "Trích xuất văn bản"
4. View extracted text
5. Copy to clipboard or download as text file

### Using the API

```bash
# Extract text from base64 image
curl -X POST "http://localhost:8000/api/ocr/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "image_b64": "base64_encoded_image_here"
  }'

# Upload image file
curl -X POST "http://localhost:8000/api/ocr/upload" \
  -F "file=@path/to/image.jpg"
```

### Using Python

```python
import requests
import base64

# Read image
with open("image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# Make request
response = requests.post(
    "http://localhost:8000/api/ocr/extract",
    json={"image_b64": image_b64}
)

result = response.json()
print(result["text"])
```

## 🔒 Security Considerations

- Input validation on all endpoints
- File size limits (10MB default)
- CORS configuration
- Rate limiting (recommended for production)
- Authentication (recommended for production)
- HTTPS in production

## 🚀 Production Deployment

### Backend

1. Set `DEBUG=False`
2. Configure production database
3. Use gunicorn + uvicorn workers
4. Set up logging and monitoring
5. Enable HTTPS
6. Implement rate limiting
7. Add authentication

### Frontend

1. Build production bundle: `npm run build`
2. Deploy to CDN or static hosting
3. Configure environment variables
4. Set up HTTPS
5. Enable gzip compression
6. Configure caching headers

### Recommended Hosting

- **Backend**: AWS EC2, Google Cloud Run, Heroku, DigitalOcean
- **Frontend**: Vercel, Netlify, AWS S3 + CloudFront
- **Database**: PostgreSQL (if needed for logging/users)
- **Container**: AWS ECS, Google Cloud Run, Kubernetes

## 📊 Performance

- Backend response time: < 2s for typical images
- Frontend load time: < 1s
- Image processing: Depends on model and image size
- Concurrent requests: Supports multiple simultaneous users

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🐛 Troubleshooting

### Backend won't start

- Check Python version (3.11+)
- Verify all dependencies installed
- Check `.env` configuration
- Review logs for errors

### Frontend won't connect to backend

- Verify backend is running
- Check `VITE_API_URL` in frontend `.env`
- Verify CORS configuration in backend
- Check browser console for errors

### OCR not working

- Verify Modal API configuration or local model setup
- Check image format and size
- Review backend logs
- Ensure HuggingFace token is valid (if using)

### Docker issues

- Ensure Docker daemon is running
- Check port availability (3000, 8000)
- Verify Docker Compose version
- Review container logs: `docker-compose logs`

## 📞 Support

For issues, questions, or suggestions:
- Create an issue in the repository
- Check existing documentation
- Review API documentation at `/api/docs`

## 🎉 Acknowledgments

- GLM-OCR Model for Vietnamese text recognition
- FastAPI framework
- React and Vite teams
- Open source community

---

**Built with ❤️ for the OCR community**