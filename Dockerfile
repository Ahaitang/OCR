FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgomp1 libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
RUN mkdir -p /app/app/models/pretrained

ENV PYTHONUNBUFFERED=1
ENV DB_HOST=mysql
ENV DB_PORT=3306

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]