@echo off
cd /d %~dp0

if not exist .env copy .env.example .env

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload