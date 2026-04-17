# YOLOv8n Integration with Flutter App

## Overview
The Flutter app communicates with a Python Flask backend that runs YOLOv8n model. The backend processes camera frames and sends detection results back to the app.

```
Flutter App (Mobile)
      ↓ HTTP (camera frames)
  Backend Service (Python)
      ↓ Uses YOLOv8n model
  Detection Results ← Camera IP
```

---

## 📋 Prerequisites

### 1. YOLOv8n Model File
✅ **Location**: `best_model/best.pt`

The backend is configured to load the model from this path:
```python
CUSTOM_MODEL_PATH = os.path.join("..", "best_model", "best.pt")  # YOLOv8n fine-tuned model
```

### 2. Python Dependencies
Ensure you have installed:
```bash
pip install ultralytics opencv-python flask flask-cors numpy torch
```

---

## 🚀 Step-by-Step Integration

### Step 1: Train YOLOv8n Model (if you don't have best.pt yet)

**Run the training script:**
```bash
cd "c:\Users\Priyanka\Documents\project data"
python train3.py
```

**What happens:**
- Trains YOLOv8n on your custom dataset (1,636 images, 20 classes)
- Creates model in: `runs/detect_yolov8n/weights/best.pt`
- Automatically copies to: `best_model/best.pt`
- Training takes ~30-60 minutes on GPU

**Options to skip training:**
- If you already have a trained YOLOv8n model, copy it to `best_model/best.pt`
- If using pretrained (untrained) YOLOv8n: the backend will download automatically

---

### Step 2: Start the Backend Service

**Open Terminal in project directory:**
```bash
cd "c:\Users\Priyanka\Documents\project data\Navigation App"
```

**Start the backend:**
```bash
python backend_service.py
```

**Expected output:**
```
============================================================
BACKEND SERVICE STARTUP
============================================================
[1/4] PyTorch CUDA enabled - Using GPU if available
[2/4] Flask imported successfully
[3/4] Loading PyTorch and YOLO... (this may take 10-30 seconds)
     ✓ PyTorch imported
[3.1/4] Inference device selected: cuda:0
[4/4] Loading YOLOv8n model...

  📦 YOLOv8n Model: ..\ best_model\best.pt (exists: True)
      ✅ YOLOv8n model loaded (20 classes)

============================================================
✅ BACKEND READY - YOLOv8n model loaded on port 5000
============================================================

📋 CUSTOM MODEL CLASS NAMES (for verification):
   Class 0: 'Door'
   Class 1: 'Human'
   ...
   Class 19: '...'
```

**If backend fails to start:**
```bash
# Check if port 5000 is already in use
netstat -ano | findstr :5000

# Kill the process if needed
taskkill /PID <PID> /F

# Try again
python backend_service.py
```

---

### Step 3: Get Your PC's IP Address

**Find your PC's IP (Windows):**
```bash
# Open PowerShell and run:
ipconfig
```

**Look for:**
```
IPv4 Address. . . . . . . . . . : 192.168.x.x
                                  (or similar)
```

**Or use this Python script:**
```python
import socket
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
print(f"Your PC IP: {ip}")
```

---

### Step 4: Connect Flutter App to Backend

**Run Flutter app with backend configuration:**

```bash
cd "c:\Users\Priyanka\Documents\project data\Navigation App"

# Replace 192.168.x.x with your actual PC IP from Step 3
flutter run \
  --dart-define=BACKEND_IP=192.168.x.x \
  --dart-define=BACKEND_PORT=5000
```

**For Windows PowerShell (single line):**
```powershell
flutter run --dart-define=BACKEND_IP=192.168.x.x --dart-define=BACKEND_PORT=5000
```

**Example (if your PC IP is 192.168.1.100):**
```bash
flutter run --dart-define=BACKEND_IP=192.168.1.100 --dart-define=BACKEND_PORT=5000
```

**What the app does:**
- Connects to backend at `http://192.168.1.100:5000`
- Sends camera frames as base64 JPEG images
- Receives detection results (objects, positions, distances)
- Displays objects on screen with bounding boxes

---

## ✅ Verify Integration is Working

### In Backend Terminal:
You should see messages like:
```
========================================================
📨 INCOMING REQUEST - Frame received from app
========================================================
✓ Frame decoded successfully: (720, 960, 3)
⏱️  Decode time: 2.34ms

🔍 EDGE DETECTION (Sobel):
⏱️  Edge detection time: 1.23ms

⏱️  TIMING | YOLOv8n inference: 15.45ms | Raw detections: 3
```

### In Flutter App:
- App displays green "✓ Connected" status
- Camera feed shows detected objects with boxes
- Objects are labeled (Door, Human, Chair, etc.)
- Distance estimates appear for each object

---

## 🔧 Troubleshooting

### Problem 1: "Could not connect to backend"

**Solution:**
```bash
# 1. Check if backend is running
# Look for "✅ BACKEND READY" message in backend terminal

# 2. Verify correct IP address
ipconfig  # Get your PC IP

# 3. Make sure firewall isn't blocking port 5000
# Windows: Settings → Firewall → Allow app through firewall → Python

# 4. Test connection manually
python -c "import requests; print(requests.get('http://192.168.x.x:5000/health').json())"
```

### Problem 2: "Model not loaded" error

**Solution:**
```bash
# 1. Check if best.pt exists
dir "best_model"  # Should show best.pt

# 2. If missing, train the model
python train3.py

# 3. Or download pretrained YOLOv8n (will auto-download)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# 4. Then copy to best_model
copy "path/to/yolov8n.pt" "best_model/best.pt"
```

### Problem 3: "Slow detection / High latency"

**Solution:**
```bash
# Use GPU instead of CPU
# Backend automatically uses GPU if available
# Verify in backend output: "Inference device selected: cuda:0"

# If using CPU, reduce image size
# Edit backend_service.py, line ~380:
# Change: results = model(frame, ...)
# To: results = model(frame, imgsz=320, ...)  # Smaller = faster
```

### Problem 4: "App can't access backend (network issue)"

**Solution:**
```bash
# 1. Make sure both devices are on same WiFi
# Phone and PC must be on same network

# 2. Disable firewall temporarily for testing
# Windows: Settings → Windows Security → Firewall

# 3. Check if backend is accessible from phone
# On phone, open browser:
# http://192.168.x.x:5000/health
# Should return: {"status": "healthy"}

# 4. If using VPN, disable it
```

---

## 📊 API Endpoints

The Flutter app can use these backend endpoints:

### Health Check
```
GET /health
Response: {"status": "healthy"}
```

### Object Detection
```
POST /detect
Body: {"image": "base64_encoded_jpeg"}
Response: {
  "detections": [
    {
      "name": "Door",
      "confidence": 0.95,
      "bbox": [x1, y1, x2, y2],
      "distance": 2.5
    }
  ]
}
```

### Test Backend Connection
```bash
# From Python
import requests
response = requests.get('http://192.168.1.100:5000/health')
print(response.json())
```

---

## 📱 Flutter App Configuration

The flutter app reads backend settings from environment variables:

```dart
// In detection_service.dart
static const String baseIP = 
    String.fromEnvironment('BACKEND_IP', defaultValue: '10.26.67.141');
static const int port = 
    int.fromEnvironment('BACKEND_PORT', defaultValue: 5000);
```

**Override at runtime:**
```bash
flutter run \
  --dart-define=BACKEND_IP=192.168.1.100 \
  --dart-define=BACKEND_PORT=5000
```

---

## 🎯 Complete Workflow

```
1. Terminal 1: Start Backend
   └─ python backend_service.py
      └─ ✅ Backend ready on port 5000

2. Terminal 2: Start Flutter App
   └─ flutter run --dart-define=BACKEND_IP=192.168.x.x --dart-define=BACKEND_PORT=5000
      └─ ✅ App connects to backend

3. Mobile Device: Camera Detection
   └─ Points camera at objects
      └─ Backend detects objects using YOLOv8n
         └─ App displays results
```

---

## 📈 Performance Tips

1. **Faster Detection:**
   - Use GPU (automatically enabled if available)
   - Backend should show: `Inference device selected: cuda:0`

2. **Better Accuracy:**
   - Ensure good lighting
   - Point camera directly at objects
   - Keep distance between 0.5m - 10m

3. **Network Optimization:**
   - Phone and PC on same WiFi (2.4GHz better than 5GHz for range)
   - Keep phone close to router
   - Reduce image compression if needed

---

## 🎓 Model Details

**YOLOv8n Specifications:**
- **Size:** 6.3 MB
- **Parameters:** 3.3M
- **Inference Speed:** 5-10ms per frame
- **Input Size:** 640×640 (resized by model)
- **Classes:** 20 (custom: Door, Human, Chair, Table, Sofa, etc.)

**Model Location in Code:**
```python
# backend_service.py (Line ~55)
CUSTOM_MODEL_PATH = os.path.join("..", "best_model", "best.pt")
custom_model = YOLO(CUSTOM_MODEL_PATH)
```

---

## ✨ Next Steps

✅ **Phase 1 - Setup (You are here)**
- Train YOLOv8n model (or use existing)
- Start backend service
- Connect Flutter app

✅ **Phase 2 - Testing**
- Test object detection accuracy
- Adjust confidence thresholds if needed
- Fine-tune distance estimation

✅ **Phase 3 - Deployment**
- Package Flutter app for production
- Deploy backend to server (optional)
- Test with real-world scenarios

---

## 🆘 Support

If you encounter issues:

1. **Check backend logs** - Terminal where backend is running
2. **Check Flutter logs** - Terminal where Flutter app is running
3. **Test connectivity** - `ping 192.168.x.x` from phone
4. **Verify model** - `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`
5. **Check port** - `netstat -ano | findstr :5000`

---

**Integration Guide Complete!** 🎉

Your Flutter app should now detect objects using YOLOv8n model in real-time!
