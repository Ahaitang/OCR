#!/bin/bash
# Hospital AI Service Startup Script

cd "$(dirname "$0")"

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload