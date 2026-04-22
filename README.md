# Hospital AI Service

FastAPI service for hospital data analysis and OCR.

## Features

- QMG score trend analysis & anomaly detection
- Neuroimmune followup priority optimization
- Treatment effect evaluation
- Medical record OCR (PaddleOCR)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run service
uvicorn app.main:app --reload
```

## API Endpoints

| Path | Description |
|------|-------------|
| `/health` | Health check |
| `/api/qmg/trend/{id}` | Score trend |
| `/api/qmg/anomaly/{id}` | Anomaly detection |
| `/api/neuro/followup-priority` | Followup ranking |
| `/api/ocr/parse` | OCR parsing |

## Docker

```bash
docker build -t hospital-ai .
docker run -p 8000:8000 hospital-ai
```