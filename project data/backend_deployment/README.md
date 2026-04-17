# Backend Deployment Guide

This folder contains all files needed to deploy your YOLO object detection backend to Google Cloud Run or other cloud platforms.

---

## 📁 Folder Contents

```
backend_deployment/
├── unified_server.py        # Flask backend server (main app)
├── requirements.txt         # Python dependencies
├── Dockerfile              # For containerized deployment
├── .dockerignore           # Exclude unnecessary files from Docker build
├── models/                 # Place your model files here
│   ├── best.pt            # Your trained custom model
│   └── yolov8n.pt         # YOLOv8n model (optional)
└── README.md              # This file
```

---

## 🚀 Quick Start (Local Testing)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Your Model
- Copy your trained model to `models/` folder:
  ```bash
  cp ../best_model/best.pt models/best.pt
  ```

### 3. Run Backend Locally

```bash
python unified_server.py
```

The backend will start on `http://localhost:5000`

### 4. Test the API

```bash
# Health check
curl http://localhost:5000/health

# Detect objects (send base64 encoded image)
curl -X POST http://localhost:5000/detect \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64_encoded_image>"}'

# Switch models
curl -X POST http://localhost:5000/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "yolov8n"}'
```

---

## 🐳 Docker Deployment

### 1. Build Docker Image Locally

```bash
docker build -t my-backend:latest .
```

### 2. Test Docker Image Locally

```bash
docker run -p 8080:8080 my-backend:latest
```

Access at: `http://localhost:8080/health`

---

## ☁️ Deploy to Google Cloud Run

### Prerequisites
- Google Cloud account and project
- Google Cloud SDK installed (`gcloud`)
- Docker installed
- Model files added to `models/` folder

### Step 1: Set Up Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Set your region (e.g., us-central1)
gcloud config set run/region us-central1
```

### Step 2: Build and Push to Container Registry

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/navigation-backend:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/navigation-backend:latest
```

### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy navigation-backend \
  --image gcr.io/YOUR_PROJECT_ID/navigation-backend:latest \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 120 \
  --set-env-vars PORT=8080
```

### Step 4: Get Your Service URL

```bash
gcloud run services describe navigation-backend --format='value(status.url)'
```

This will output something like:
```
https://navigation-backend-xxxxxx.run.app
```

---

## 🔗 Update Your Flutter App

In your Flutter app's `detection_service.dart`, update the backend IP:

```dart
static const String baseIP = 'https://navigation-backend-xxxxxx.run.app';
```

---

## 📊 API Endpoints

### **GET /health**
Health check endpoint
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "current_model": "custom",
  "classes": 20,
  "available_models": ["custom", "yolov8n"]
}
```

---

### **POST /detect**
Object detection endpoint

**Request:**
```json
{
  "image": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "success": true,
  "detections": [
    {
      "class": "human",
      "confidence": 0.95,
      "distance": 2.5,
      "position": {
        "x": 320,
        "y": 240,
        "x1": 200, "y1": 100,
        "x2": 440, "y2": 380
      },
      "width": 240,
      "height": 280
    }
  ],
  "navigation": {
    "direction": "FORWARD",
    "popup": {...}
  },
  "frame_size": {"width": 640, "height": 480}
}
```

---

### **POST /switch-model**
Switch between models

**Request:**
```json
{
  "model": "custom"  // or "yolov8n"
}
```

**Response:**
```json
{
  "status": "switched",
  "current_model": "custom",
  "classes": 20,
  "message": "Model custom loaded successfully"
}
```

---

## ⚙️ Environment Variables

Set these via Cloud Run CLI:

- `PORT` - HTTP port (default: 5000, Cloud Run requires 8080)
- `NAV_FOCAL_LENGTH_PX` - Camera focal length (default: 800)
- `NAV_DOOR_WIDTH_M` - Door width for distance estimation (default: 0.9)
- `NAV_DOOR_HEIGHT_M` - Door height for distance estimation (default: 2.0)

Example:
```bash
gcloud run deploy navigation-backend \
  ... \
  --set-env-vars \
    PORT=8080,\
    NAV_FOCAL_LENGTH_PX=800
```

---

## 📝 Model Files

Place your model files in the `models/` directory:

- `models/best.pt` - Your trained custom model (required)
- `models/yolov8n.pt` - YOLOv8n model (optional, will auto-download if not present)

---

## 🔍 Troubleshooting

### Model not loading
- Ensure `models/best.pt` exists
- Check file permissions
- Verify model format (.pt file)

### Docker build fails
- Update `requirements.txt` versions if needed
- Check internet connection
- Ensure 4GB+ free disk space

### Cloud Run deployment fails
- Check project ID is correct
- Ensure model files are included
- Increase memory allocation if needed (use `--memory 4Gi`)

### High latency
- Increase Cloud Run memory: `--memory 8Gi`
- Use a larger machine type instance
- Enable GPU acceleration (if available in your region)

---

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Docs](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)

---

## ✅ Deployment Checklist

- [ ] Copy model files to `models/best.pt`
- [ ] Test backend locally: `python unified_server.py`
- [ ] Build Docker image: `docker build -t my-backend .`
- [ ] Authenticate with Google Cloud: `gcloud auth login`
- [ ] Build and push to registry: `docker push gcr.io/...`
- [ ] Deploy to Cloud Run: `gcloud run deploy ...`
- [ ] Get service URL from Cloud Console
- [ ] Update Flutter app with new backend URL
- [ ] Test from Flutter app
- [ ] Monitor Cloud Run logs: `gcloud run logs read navigation-backend`

---

**Need help?** Check the main project documentation or cloud provider support.
