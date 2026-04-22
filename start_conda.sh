#!/bin/bash
# Hospital AI Service Startup Script (Conda Environment)

cd "$(dirname "$0")"

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate hospital-ai

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Start service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload