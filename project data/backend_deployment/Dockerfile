# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Download YOLOv8n model to avoid runtime download
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" || true

# Expose port (Cloud Run requires 8080, local testing uses 5000)
EXPOSE 8080

# Set environment variable for Cloud Run
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run the application
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gthread --timeout 120 unified_server:app
