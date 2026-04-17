# Google Cloud Run Deployment Guide

Complete step-by-step guide to deploy your backend to Google Cloud Run.

---

## Prerequisites Checklist

- [ ] Google Cloud Account (with billing enabled)
- [ ] Google Cloud SDK installed
- [ ] Docker installed
- [ ] Git installed
- [ ] Model file ready (`best.pt`)
- [ ] Flutter app developer environment

---

## Step 1: Prepare Your Model

### 1.1 Copy Model Files

```bash
# From your project root:
cp ../best_model/best.pt models/best.pt
```

Verify the file exists:
```bash
ls -la models/best.pt
```

---

## Step 2: Test Locally

### 2.1 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.2 Run Backend

On **Windows:**
```bash
start_backend.bat
```

On **Linux/Mac:**
```bash
bash start_backend.sh
```

### 2.3 Test API

Open a new terminal:
```bash
# Test health endpoint
curl http://localhost:5000/health

# Should return:
# {
#   "status": "healthy",
#   "model_loaded": true,
#   "current_model": "custom",
#   "classes": 20,
#   "available_models": ["custom", "yolov8n"]
# }
```

---

## Step 3: Set Up Google Cloud

### 3.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter project name: `navigation-app-backend`
5. Click "CREATE"
6. Wait for project to be created

### 3.2 Enable Required APIs

```bash
# Set your project ID
export PROJECT_ID="navigation-app-backend"

gcloud config set project $PROJECT_ID

# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Enable Compute Engine API (for resources)
gcloud services enable compute.googleapis.com
```

### 3.3 Authenticate Docker

```bash
gcloud auth configure-docker gcr.io
```

---

## Step 4: Build and Push Docker Image

### 4.1 Build Docker Image

```bash
# Set your project ID
export PROJECT_ID="navigation-app-backend"

# Build image
docker build -t gcr.io/$PROJECT_ID/navigation-backend:latest .

# Verify build succeeded
docker images | grep navigation-backend
```

### 4.2 Test Docker Image Locally

```bash
# Run container
docker run -p 8080:8080 gcr.io/$PROJECT_ID/navigation-backend:latest

# In another terminal, test:
curl http://localhost:8080/health

# Stop container (Ctrl+C in first terminal)
```

### 4.3 Push to Google Container Registry

```bash
docker push gcr.io/$PROJECT_ID/navigation-backend:latest

# Verify upload (may take a minute)
gcloud container images list
```

---

## Step 5: Deploy to Google Cloud Run

### 5.1 Deploy Service

```bash
export PROJECT_ID="navigation-app-backend"

gcloud run deploy navigation-backend \
  --image gcr.io/$PROJECT_ID/navigation-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 120 \
  --set-env-vars PORT=8080 \
  --max-instances 10 \
  --min-instances 1
```

Wait for deployment to complete...

### 5.2 Get Service URL

```bash
gcloud run services describe navigation-backend \
  --platform managed \
  --region us-central1 \
  --format='value(status.url)'
```

Save this URL! It will look like:
```
https://navigation-backend-xxxxxx.run.app
```

---

## Step 6: Test Cloud Deployment

### 6.1 Test Health Endpoint

```bash
# Replace with your URL from Step 5.2
export BACKEND_URL="https://navigation-backend-xxxxxx.run.app"

curl $BACKEND_URL/health
```

### 6.2 Check Logs

```bash
gcloud run logs read navigation-backend \
  --platform managed \
  --region us-central1 \
  --limit 50
```

---

## Step 7: Update Flutter App

### 7.1 Update Backend URL in Flutter

Edit `Navigation App/lib/services/detection_service.dart`:

```dart
class DetectionService {
  static const String baseIP = "navigation-backend-xxxxxx.run.app";  // Your Cloud Run URL (without https://)
  static const int port = 443;  // HTTPS port
```

Change from HTTP to HTTPS in baseUrl getter:
```dart
static String get baseUrl => 'https://$baseIP:$port';
```

### 7.2 Rebuild Flutter App

```bash
cd Navigation App
flutter pub get
flutter run
```

---

## Step 8: Monitor & Maintain

### 8.1 View Logs

```bash
gcloud run logs read navigation-backend --platform managed --region us-central1 --tail
```

### 8.2 View Metrics

```bash
gcloud monitoring dashboards list
```

### 8.3 Update Deployment

If you make changes to your code:

```bash
export PROJECT_ID="navigation-app-backend"

# Rebuild and push
docker build -t gcr.io/$PROJECT_ID/navigation-backend:latest .
docker push gcr.io/$PROJECT_ID/navigation-backend:latest

# Redeploy (uses new image)
gcloud run deploy navigation-backend \
  --image gcr.io/$PROJECT_ID/navigation-backend:latest \
  --platform managed \
  --region us-central1
```

---

## Troubleshooting

### Issue: Model not loading in Cloud Run

**Solution:** Ensure `models/best.pt` exists locally before building Docker image

```bash
ls -la models/best.pt  # Should exist
docker build -t ... .  # Then rebuild
```

### Issue: 403 Permission Denied

**Solution:** Check authentication:
```bash
gcloud auth login
gcloud auth application-default login
```

### Issue: Container fails to start

**Solution:** Check logs:
```bash
gcloud run logs read navigation-backend --platform managed --region us-central1 --limit 100
```

### Issue: Slow inference

**Solution:** Increase resources in deployment:
```bash
gcloud run deploy navigation-backend \
  ... \
  --memory 8Gi \
  --cpu 4 \
  --max-instances 5
```

---

## Cost Estimates (as of 2024)

- **Cloud Run compute:** $0.00002400/vCPU-second + $0.0000025/GB-second
- Average request: 2-5 seconds → ~$0.0001-0.0002 per inference
- 10,000 requests/month ≈ $1-2 USD
- Check [Cloud Run Pricing](https://cloud.google.com/run/pricing)

---

## Quick Reference Commands

```bash
# Deploy
gcloud run deploy navigation-backend --image gcr.io/PROJECT_ID/navigation-backend:latest

# Get URL
gcloud run services describe navigation-backend --format='value(status.url)'

# View logs
gcloud run logs read navigation-backend --tail

# Delete service
gcloud run services delete navigation-backend

# Update env variables
gcloud run deploy navigation-backend --set-env-vars KEY=VALUE

# Scale settings
gcloud run deploy navigation-backend --min-instances 1 --max-instances 10

# View metrics
gcloud monitoring dashboards list
```

---

## Next Steps

1. ✅ Verify Cloud Run deployment is returning detection results
2. ✅ Update Flutter app backend URL
3. ✅ Test end-to-end: Flutter app → Cloud Run → Model → Result
4. ✅ Monitor logs for errors
5. ✅ Set up alerts for failures
6. ✅ Implement CI/CD for automatic deployment

---

**Need Help?**
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting)
- [Cloud Support](https://cloud.google.com/support)
