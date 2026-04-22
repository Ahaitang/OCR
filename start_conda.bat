@echo off
REM Hospital AI Service Startup Script (Conda Environment)

cd /d %~dp0

REM Activate conda environment
call conda activate hospital-ai

REM Create .env if not exists
if not exist .env copy .env.example .env

REM Start service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload