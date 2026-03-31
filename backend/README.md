# OCR Service - Backend

Professional FastAPI backend for OCR text extraction service using Modal API.

## Features

- Fast and efficient OCR processing via Modal API
- Support for multiple image formats
- RESTful API with comprehensive documentation
- Input validation and error handling
- Automatic retry logic with exponential backoff
- Automatic API documentation (Swagger/ReDoc)
- Comprehensive logging
- Docker support

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

