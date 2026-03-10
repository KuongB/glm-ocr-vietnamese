# OCR Service - Backend

Professional FastAPI backend for OCR text extraction service using Modal API.

## Features

- 🚀 Fast and efficient OCR processing via Modal API
- 📝 Support for multiple image formats
- 🌐 RESTful API with comprehensive documentation
- 🔒 Input validation and error handling
- 🔄 Automatic retry logic with exponential backoff
- 📊 Automatic API documentation (Swagger/ReDoc)
- 📝 Comprehensive logging
- 🐳 Docker support

## Architecture

This backend acts as a proxy service that:
1. Receives images from frontend
2. Validates and processes images
3. Sends images to Modal API (serverless GPU)
4. Returns extracted text to frontend

**No local ML dependencies required** - all inference happens on Modal.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── routes/
│   │   ├── ocr.py          # OCR endpoints
│   │   └── health.py       # Health check endpoints
│   └── services/
│       └── ocr_service.py  # Business logic
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── Dockerfile              # Docker configuration
```

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your Modal API URL
```

**Important**: You must set `MODAL_API_URL` in `.env` file.

Get your Modal API URL by deploying the model:
```bash
modal deploy serve.py
```

See [../MODAL_DEPLOYMENT.md](../MODAL_DEPLOYMENT.md) for deployment instructions.

### 4. Run the server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /api/health` - Check service health
- `GET /api/` - Root endpoint with API info

### OCR Operations
- `POST /api/ocr/extract` - Extract text from base64 image
- `POST /api/ocr/upload` - Upload and extract text from image file
- `GET /api/ocr/supported-languages` - Get supported languages

### Documentation
- `GET /api/docs` - Swagger UI documentation
- `GET /api/redoc` - ReDoc documentation

## Usage Examples

### Extract text from base64 image

```bash
curl -X POST "http://localhost:8000/api/ocr/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "image_b64": "your_base64_encoded_image_here",
    "language": "vi"
  }'
```

### Upload image file

```bash
curl -X POST "http://localhost:8000/api/ocr/upload" \
  -F "file=@path/to/image.jpg"
```

## Docker Deployment

### Build image

```bash
docker build -t ocr-backend .
```

### Run container

```bash
docker run -p 8000:8000 --env-file .env ocr-backend
```

## Configuration

Key environment variables in `.env`:

- `APP_NAME`: Application name
- `DEBUG`: Debug mode (True/False)
- `CORS_ORIGINS`: Allowed origins for CORS (comma-separated)
- `MAX_IMAGE_SIZE`: Maximum image size in bytes (default: 10MB)
- `MODAL_API_URL`: **REQUIRED** - Modal API endpoint URL
- `MODAL_TOKEN`: Optional authorization token for Modal API
- `MODAL_TIMEOUT`: Request timeout in seconds (default: 60)
- `MODAL_MAX_RETRIES`: Number of retry attempts (default: 3)

### Example `.env`

```env
APP_NAME=OCR Service API
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_IMAGE_SIZE=10485760

# Get this URL from: modal deploy serve.py
MODAL_API_URL=https://username--glm-ocr-api-ocr-endpoint.modal.run
MODAL_TOKEN=
MODAL_TIMEOUT=60
MODAL_MAX_RETRIES=3
```

## Development

### Run tests

```bash
pytest
```

### Code formatting

```bash
black app/ main.py
flake8 app/ main.py
```

## Production Deployment

For production, consider:

1. Set `DEBUG=False`
2. Use a production ASGI server (Gunicorn + Uvicorn workers)
3. Configure proper CORS origins
4. Set up logging and monitoring
5. Use HTTPS
6. Implement rate limiting
7. Add authentication if needed

## License

MIT
