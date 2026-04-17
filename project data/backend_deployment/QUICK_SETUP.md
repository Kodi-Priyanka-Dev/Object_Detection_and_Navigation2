# Quick Setup Instructions

## 📋 Complete Checklist

### Local Testing

- [ ] Copy model to `models/best.pt`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start backend: `python unified_server.py` or `./start_backend.sh`
- [ ] Test API: `python test_api.py`
- [ ] Verify health: `curl http://localhost:5000/health`

### Docker Testing

- [ ] Build image: `docker build -t navigation-backend:latest .`
- [ ] Run container: `docker run -p 8080:8080 navigation-backend:latest`
- [ ] Test health: `curl http://localhost:8080/health`

### Google Cloud Deployment

- [ ] Install Google Cloud SDK
- [ ] Authenticate: `gcloud auth login`
- [ ] Create project: `gcloud projects create navigation-app-backend`
- [ ] Set project: `gcloud config set project navigation-app-backend`
- [ ] Enable APIs: `gcloud services enable run.googleapis.com containerregistry.googleapis.com`
- [ ] Configure Docker: `gcloud auth configure-docker gcr.io`
- [ ] Build image: `docker build -t gcr.io/navigation-app-backend/navigation-backend:latest .`
- [ ] Push image: `docker push gcr.io/navigation-app-backend/navigation-backend:latest`
- [ ] Deploy: `gcloud run deploy navigation-backend --image gcr.io/navigation-app-backend/navigation-backend:latest --platform managed --allow-unauthenticated --memory 4Gi`
- [ ] Get URL: `gcloud run services describe navigation-backend --format='value(status.url)'`
- [ ] Update Flutter app with new URL

---

## 📁 File Structure

```
backend_deployment/
├── unified_server.py          ← Main backend server
├── requirements.txt           ← Python dependencies
├── Dockerfile                 ← Container configuration
├── docker-compose.yml         ← Local Docker setup
├── .dockerignore              ← Docker build exclusions
├── .gitignore                 ← Git exclusions
├── test_api.py               ← API testing script
├── start_backend.bat         ← Windows startup
├── start_backend.sh          ← Linux/Mac startup
├── models/                   ← Model files directory
│   └── best.pt              ← Your trained model (ADD THIS)
├── README.md                 ← Project documentation
├── DEPLOYMENT_GUIDE.md       ← Detailed deployment steps
└── QUICK_SETUP.md           ← This file
```

---

## 🎯 Quick Start (30 seconds)

### Windows
```batch
copy ..\best_model\best.pt models\best.pt
call start_backend.bat
```

### Linux/Mac
```bash
cp ../best_model/best.pt models/best.pt
bash start_backend.sh
```

---

## 🔗 API Quick Reference

### Health Check
```bash
curl http://localhost:5000/health
```

### Object Detection
```bash
curl -X POST http://localhost:5000/detect \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### Switch Models
```bash
curl -X POST http://localhost:5000/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "yolov8n"}'
```

---

## 🐳 Docker Compose (Single Command)

```bash
# Build and run locally
docker-compose up --build

# Access at http://localhost:8080
# View logs: docker-compose logs -f
# Stop: Ctrl+C then `docker-compose down`
```

---

## ☁️ Google Cloud One-Liner

After setting up gcloud:
```bash
docker build -t gcr.io/$PROJECT_ID/navigation-backend:latest . && \
docker push gcr.io/$PROJECT_ID/navigation-backend:latest && \
gcloud run deploy navigation-backend --image gcr.io/$PROJECT_ID/navigation-backend:latest --platform managed --allow-unauthenticated --memory 4Gi --timeout 120
```

Then get URL:
```bash
gcloud run services describe navigation-backend --format='value(status.url)'
```

---

## 🧪 Test Everything

```bash
# Start backend in Terminal 1
python unified_server.py

# In Terminal 2, run tests
python test_api.py
```

---

## 📊 Environment Variables

Set these via `--set-env-vars` in Cloud Run:

```
PORT=8080                           # HTTP port
NAV_FOCAL_LENGTH_PX=800            # Camera focal length
NAV_DOOR_WIDTH_M=0.9               # Door width (meters)
NAV_DOOR_HEIGHT_M=2.0              # Door height (meters)
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Backend not running - start with `python unified_server.py` |
| "Model not found" | Copy `best.pt` to `models/` folder |
| "Port already in use" | Kill process or use different port |
| "Docker build fails" | Check internet, increase disk space, update Docker |
| "Cloud Run deployment fails" | Check project ID, enable APIs, verify image push |
| "Slow inference" | Increase Cloud Run memory/CPU or use GPU |

---

## 📱 Update Flutter App

Edit `lib/services/detection_service.dart`:

```dart
// For local testing:
static const String baseIP = 'localhost';
static const int port = 5000;

// For Cloud Run:
static const String baseIP = 'navigation-backend-xxxxx.run.app';
static const int port = 443;
// Change baseUrl to use HTTPS
```

---

## 🚀 Deployment Summary

1. **Local**: `python unified_server.py` → Works immediately
2. **Docker**: `docker-compose up` → Works on any machine with Docker
3. **Cloud Run**: Single command → Globally accessible HTTPS endpoint

---

## 📞 Support

- Check README.md for detailed documentation
- See DEPLOYMENT_GUIDE.md for complete Google Cloud instructions
- Run `python test_api.py` to validate everything works
- Check logs: `gcloud run logs read navigation-backend --tail`

---

**Next Step**: Copy your model file and run tests!

```bash
cp ../best_model/best.pt models/best.pt
python test_api.py
```
