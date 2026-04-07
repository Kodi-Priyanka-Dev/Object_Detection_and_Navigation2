# Backend Service - Indoor Navigation System

![Backend Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Model](https://img.shields.io/badge/Model-YOLOv8s-blue)
![Framework](https://img.shields.io/badge/Framework-Flask-orange)
![GPU](https://img.shields.io/badge/GPU-CUDA%20Ready-green)

Unified Flask backend service for real-time object detection and indoor navigation guidance using **YOLOv8s** (20 custom indoor classes) with edge detection analysis.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Models Configuration](#models-configuration)
- [Performance Metrics](#performance-metrics)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The backend service provides **real-time object detection** for a Flutter mobile app, enabling blind/visually-impaired users to navigate indoors. It:

- **Detects 20 object classes** (custom indoor objects: Doors, Humans, Chairs, Tables, Sofas, Walls, etc.)
- **Estimates distances** to detected objects using focal length calculations
- **Analyzes structural features** (walls, doorways, obstructions) via edge detection
- **Generates navigation instructions** with popups and directional guidance
- **Runs on NVIDIA GPU** (RTX A2000 12GB tested) for fast inference (~8.4ms/frame)

### Single Model Approach

The backend runs **YOLOv8s exclusively**:

- **YOLOv8s (22MB)** - 20 custom indoor classes: Doors, Humans, Chairs, Tables, Sofas, Walls, etc.
- **Direct inference** - Single model, no model switching
- **Optimized performance** - Faster inference, lower memory usage
- **Better accuracy** - +6% vs YOLOv8n nano variant

---

## 🏗️ Architecture

```
Flutter App (Mobile)
        ↓
    HTTP + base64 image
        ↓
┌─────────────────────────────────────────┐
│        Flask Backend (Port 5000)         │
├─────────────────────────────────────────┤
│           YOLOv8s Model                  │
│      (20 Custom Indoor Classes)          │
│  Doors, Humans, Chairs, Tables, etc.     │
│         └──────────────┘                 │
│                ↓                         │
│    ┌─────────────────────────┐         │
│    │  Distance Estimation    │         │
│    │  (Focal Length Calc)    │         │
│    └─────────────────────────┘         │
│         ↓                               │
│    ┌─────────────────────────┐         │
│    │  Edge Detection (Sobel) │         │
│    │  Structural Analysis    │         │
│    └─────────────────────────┘         │
│         ↓                               │
│    ┌─────────────────────────┐         │
│    │  Navigation Logic       │         │
│    │  Popup Generation       │         │
│    └─────────────────────────┘         │
└─────────────────────────────────────────┘
        ↓
  JSON Response
        ↓
    Flutter App
```

---

## ✨ Key Features

### 1. **Single Model Detection**
| Model | Size | Classes | Speed | Accuracy |
|-------|------|---------|-------|----------|
| YOLOv8s | 21.5MB | 20 indoor | 8.4ms | Good (+6% vs nano) |

### 2. **Intelligent Distance Estimation**
- Uses **focal length calibration** (800px focal length)
- Per-class width estimates: Door=0.9m, Human=0.5m, Sofa=1.5m, etc.
- Formula: `distance = (real_width * focal_length) / pixel_width`

### 3. **Edge Detection & Structural Analysis**
- **Sobel edge detection** for wall/doorway analysis
- Detects obstruction levels (low/medium/high)
- Identifies potential doorway gaps
- Analyzes wall density in multiple frame sections

### 4. **Real-Time Navigation**
- **Door detection popups** - "Do you want to go through this door?"
- **Human avoidance** - Suggests left/right/stop based on position
- **Directional guidance** - STRAIGHT, LEFT, RIGHT, TURN_AROUND arrows
- **Confidence filtering** - Tuned thresholds per object class

### 5. **Performance Optimized**
- **GPU acceleration** via CUDA (auto-detects RTX A2000, A100, etc.)
- **Frame caching** in GPU memory for speed
- **NMS deduplication** to prevent duplicate detections
- **Total latency**: ~150ms per frame (decode + inference + processing)

---

## 📦 Installation

### Prerequisites

- **Python 3.9+** (tested with 3.12)
- **NVIDIA GPU** with CUDA 11.8+ (optional, falls back to CPU)
- **Windows/Linux/Mac**

### Step 1: Install Dependencies

```bash
cd "Navigation App"
pip install -r backend_requirements.txt
```

**Dependencies:**
- `flask` - Web framework
- `flask-cors` - CORS support for mobile app
- `ultralytics` - YOLOv8 library
- `torch` - Deep learning framework
- `torchvision` - Computer vision utilities
- `opencv-python` - Image processing
- `numpy` - Numerical computing

Alternatively, install manually:

```bash
pip install flask flask-cors ultralytics torch torchvision opencv-python numpy
```

### Step 2: Prepare Models

The backend expects two models:

**Custom Model:**
```
../best_model/best.pt  (YOLOv8s fine-tuned on 20 indoor classes)
```
This is automatically downloaded/created when you run `python train3.py`

**COCO Model:**
```
yolov8n.pt  (Auto-downloaded on first run from Ultralytics)
```

### Step 3: Verify Installation

```bash
python backend_service.py
```

Expected output:
```
============================================================
BACKEND SERVICE STARTUP
============================================================
[1/4] PyTorch CUDA enabled - Using GPU if available
[2/4] Flask imported successfully
[3/4] Loading PyTorch and YOLO...
[4/4] Loading TWO models for unified detection...

✅ UNIFIED BACKEND READY - Both models loaded on port 5000
```

---

## 🚀 Quick Start

### Start Backend Server

```bash
cd "Navigation App"
python backend_service.py
```

The server will:
1. Load both YOLOv8s and YOLOv8n models (takes ~10-30 seconds)
2. Verify GPU availability and select device (CUDA or CPU)
3. Print loaded class names for verification
4. Listen on `http://0.0.0.0:5000`

### Run Flutter App

In another terminal:

```bash
cd "Navigation App"
flutter run
```

The app will automatically connect to the backend at `http://localhost:5000`

### Monitor Logs

Backend logs show:
- Frame decode time (ms)
- Edge detection analysis
- Raw model outputs (before filtering)
- Detection confidence values
- NMS deduplication decisions
- Navigation logic decisions
- Total request latency

---

## 🔌 API Endpoints

### 1. **Health Check**

```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "model_loaded": true
}
```

---

### 2. **Object Detection** (Main Endpoint)

```http
POST /detect
Content-Type: application/json

{
    "image": "<base64-encoded-jpg-image>"
}
```

**Request Format:**
- Image must be base64 encoded (from Flutter camera frame)
- Recommended size: 640x480 to 1280x720

**Response Format:**
```json
{
    "success": true,
    "detections": [
        {
            "class": "Door",
            "confidence": 0.85,
            "position": {
                "x": 320,
                "y": 240,
                "x1": 200,
                "y1": 100,
                "x2": 440,
                "y2": 380,
                "center_x": 320,
                "center_y": 240
            },
            "distance": 1.23,
            "width": 240,
            "height": 280
        },
        {
            "class": "Human",
            "confidence": 0.92,
            "position": {"x": 640, "y": 360, ...},
            "distance": 2.15,
            "width": 100,
            "height": 150
        }
    ],
    "navigation": {
        "direction": "STRAIGHT",
        "arrow": "FORWARD",
        "message": null,
        "popup": {
            "type": "door",
            "message": "🚪 Door detected at 1.23 meters",
            "question": "Do you want to go through this door?",
            "distance": 1.23,
            "confidence": 0.85,
            "position": {"x": 320, "y": 240, ...},
            "options": ["Yes", "No"],
            "action_url": "/handle_door_response"
        }
    },
    "frame_size": {
        "width": 1280,
        "height": 720
    },
    "edge_detection": {
        "edge_percentage": 12.45,
        "edge_strength": 85.3,
        "obstruction_level": "low",
        "potential_doorways": 1,
        "walls": [
            {
                "location": "ceiling",
                "edge_density": 15.2
            },
            {
                "location": "floor",
                "edge_density": 18.9
            }
        ]
    }
}
```

**Key Fields:**

| Field | Description |
|-------|-------------|
| `detections[]` | Array of detected objects with positions and distances |
| `navigation.direction` | STRAIGHT, LEFT, RIGHT, STOP, TURN_AROUND |
| `navigation.arrow` | Navigation visual indicator |
| `navigation.popup` | User interaction popup (door/human) |
| `edge_detection` | Structural analysis (walls, doorways, obstruction) |

**Confidence Thresholds** (per-class filtering):
- Door: 0.02 (accept all detections)
- Human: 0.04
- Chair/Table: 0.03-0.05
- Backpack/Bottle/Handbag: 0.05
- Other: 0.03

---

### 3. **Handle Door Response**

```http
POST /handle_door_response
Content-Type: application/json

{
    "user_response": "yes",
    "door_class": "Door",
    "door_distance": 1.23
}
```

**Responses:**

If `user_response == "yes"`:
```json
{
    "success": true,
    "action": "proceed",
    "direction": "STRAIGHT",
    "message": "✓ Proceeding through Door...",
    "navigation": {
        "direction": "STRAIGHT",
        "arrow": "FORWARD",
        "next_steps": "Navigate through door opening"
    }
}
```

If `user_response == "no"`:
```json
{
    "success": true,
    "action": "avoid",
    "direction": "TURN_AROUND",
    "message": "✗ Finding alternate route...",
    "navigation": {
        "direction": "TURN_AROUND",
        "arrow": "BACKWARD",
        "next_steps": "Searching for alternative path"
    }
}
```

---

### 4. **Edge Detection Analysis**

```http
POST /edge_detection
Content-Type: application/json

{
    "image": "<base64-encoded-jpg-image>"
}
```

**Response:**
```json
{
    "success": true,
    "edge_stats": {
        "total_edge_pixels": 45000,
        "edge_percentage": 12.5,
        "max_edge_strength": 255,
        "mean_edge_strength": 85.3
    },
    "structural_features": {
        "obstruction_level": "low",
        "potential_doorways": 1,
        "walls": [...]
    },
    "edge_map": "<base64-encoded-edge-visualization>",
    "processing_time_ms": 8.5
}
```

---

### 5. **Live Video Feed Stream**

```http
GET /video_feed
```

Returns live MJPEG stream with detection overlays:
- Bounding boxes for all detections
- Class labels with confidence scores
- Distance estimates for doors
- Navigation arrows
- User position indicator

URL for debugging: `http://localhost:5000/video_feed`

---

### 6. **Edge Detection Live Stream**

```http
GET /edge_visualization
```

Returns live Sobel edge detection visualization:
- Binary edge map
- Wall density analysis
- Obstruction level color coding (green/orange/red)
- Potential doorway detection
- Structural feature overlays

URL for debugging: `http://localhost:5000/edge_visualization`

---

## ⚙️ Models Configuration

### ⚙️ Models Configuration

### Model Paths

Edit this in `backend_service.py`:

```python
# YOLOv8s fine-tuned on 20 custom indoor classes
CUSTOM_MODEL_PATH = os.path.join("..", "best_model", "best.pt")
```

### Custom Model Classes (20 Total)

```
 0: Digital Board       11: sofa
 1: Door               12: stand
 2: Glass Door         13: wall
 3: Machine            14: wall corner
 4: Table              15: wall edge
 5: chair              16: water filter
 6: chairs             17: window
 7: flowervase         18: wooden entrance
 8: human              19: wooden stand
 9: humans
10: round chair
```

### Distance Estimation Calibration

Edit `OBJECT_WIDTHS` dictionary to adjust distance accuracy:

```python
OBJECT_WIDTHS = {
    "door": 0.9,          # Door width in meters
    "human": 0.5,         # Average shoulder width
    "chair": 0.5,         # Chair width
    "sofa": 1.5,          # Sofa width
    "backpack": 0.35,     # Backpack width
    # ... add more classes
}

FOCAL_LENGTH = 800  # Camera focal length in pixels (calibrate for your device)
```

To **calibrate focal length**:
1. Place object of known width at known distance
2. Measure pixel width in frame
3. Calculate: `focal_length = (real_width * distance) / pixel_width`

---

## 📊 Performance Metrics

### Latency Breakdown (per request)

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| **Image decode** | 2-5 | Base64 → OpenCV |
| **Edge detection** | 8-12 | Sobel operator |
| **YOLOv8s inference** | 35-50 | YOLOv8s on GPU |
| **Distance estimation** | 0.5-1 | Math operations |
| **Navigation logic** | 1-2 | Decision making |
| **Response encoding** | 5-10 | JSON serialization |
| **Total** | ~60-120ms | Typical ~100ms |

### GPU Memory Usage

| Component | Memory |
|-----------|--------|
| YOLOv8s model | ~2 GB |
| Frame buffers | ~200 MB |
| Python/PyTorch overhead | ~1 GB |
| **Total** | ~3.2 GB |

**RTX A2000 (12GB):** ✅ Plenty of headroom
**RTX 3060 (6GB):** ✅ Sufficient
**RTX 2060 (6GB):** ⚠️ May have memory issues, reduce batch size

### Throughput

- Single image inference: ~100ms (10 FPS)
- With overhead: ~120ms per frame (8-9 actual FPS from mobile app)
- Maximum: Limited by network bandwidth to mobile device (typical 30-60ms RTT)

---

## 🔧 Troubleshooting

### Issue 1: Models Not Loading

**Symptom:**
```
❌ YOLOv8s model not loaded!
```

**Solution:**
1. Train custom model first: `python train3.py` (from project root)
2. Verify file exists: `best_model/best.pt`
3. Check path in `backend_service.py` matches your directory structure
4. Ensure YOLOv8s model is downloaded (auto-downloaded from Ultralytics on first run)

---

### Issue 2: CUDA Not Available

**Symptom:**
```
[3.1/4] Inference device selected: cpu
⚠️ CUDA GPU not detected
```

**Solutions:**
1. Verify NVIDIA GPU installed: `nvidia-smi`
2. Install CUDA Toolkit and cuDNN
3. Verify PyTorch CUDA support:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```
4. If unavailable, backend will fall back to CPU (slowest inference)

---

### Issue 3: Port 5000 Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Kill existing process on port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :5000
kill -9 <PID>

# OR change port in backend_service.py:
app.run(host='0.0.0.0', port=5001, debug=False)  # Change 5000 → 5001
```

---

### Issue 4: No Detections in Response

**Symptom:**
```json
{
    "success": true,
    "detections": [],
    "navigation": {"direction": "STRAIGHT", "popup": null}
}
```

**Checklist:**
1. Check backend logs for "RAW MODEL OUTPUT" - should show some detections at conf≥0.01
2. If raw detections exist but filtered out, lower confidence thresholds (see **Models Configuration**)
3. If no raw detections, the environment is too dark/blurry - improve lighting
4. Verify YOLOv8s model loaded correctly (logs should show 20 class names)
5. Check that `best_model/best.pt` exists and is not corrupted

---

### Issue 5: Slow Inference (~500ms+)

| Cause | Solution |
|-------|----------|
| Slow YOLOv8s inference (~100ms+) | Verify CUDA: `nvidia-smi` |
| Large input image (>1280p) | Resize in Flutter app to 640x480 |
| Low system RAM (swapping) | Close other programs |
| First run (model initialization) | Normal; ~30s on first request |
| Network latency from mobile | Use local network (not cloud backend) |

---

### Issue 6: Flask App Crashes on Demand

**Symptom:**
```python
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Close other GPU programs
2. Reduce input image size
3. Fall back to CPU:
   ```python
   INFERENCE_DEVICE = 'cpu'  # Force CPU
   ```
4. Restart the backend server

---

### Issue 7: Distance Estimation Not Accurate

**Symptom:** Objects appear much closer/farther than reported distance

**Solutions:**
1. **Calibrate focal length:**
   - Place door (0.9m wide) at exactly 2 meters
   - Note pixel width in frame
   - Calculate: `focal_length = (0.9 * 2) / pixel_width`
   - Update in code: `FOCAL_LENGTH = <calculated_value>`

2. **Adjust per-class widths:**
   - Edit `OBJECT_WIDTHS` dictionary
   - Use known dimensions from your deployment

3. **Account for camera distortion:**
   - Wide-angle cameras (~100°+ FOV) have lens distortion
   - Use camera calibration OpenCV tools

---

### Issue 8: Door/Human Popups Not Triggering

**Symptom:** Detection works but no popup generated

**Checklist:**
1. Verify detection confidence > threshold (check logs)
2. For doors: confidence must be > 0.02
3. For humans: confidence must be > 0.04
4. Check navigation logic reached "popup" generation code (view logs)
5. Verify Flutter app is listening to `/handle_door_response` endpoint

---

## 📝 Configuration Tips

### Tweak Detection Sensitivity

Lower = more detections (higher false positives), Higher = fewer detections (misses)

```python
# In /detect endpoint:
# Initial model prefilter (should be <= your lowest per-class threshold)
# You can override without code changes:
#   set MODEL_CONF_PREFILTER=0.01
custom_results = custom_model(frame, conf=MODEL_CONF_PREFILTER, device=INFERENCE_DEVICE)[0]

# Confidence thresholds per class - adjust thresholds dict
# Lower per-class thresholds = more permissive (useful for doors=0.02, humans=0.04, etc.)
CONFIDENCE_THRESHOLDS = {
    "Door": 0.02,
    "Human": 0.04,
    "Chair": 0.03,
    # ... adjust for your needs
}
```

### Tweak Distance Accuracy

```python
# Calibration constants
FOCAL_LENGTH = 800  # Larger = objects appear farther

# Per-class width estimates
OBJECT_WIDTHS = {
    "door": 0.9,    # Increase = closer distance reported
    "human": 0.5,   # Adjust to your demographic
    # ...
}
```

### Tweak Navigation Sensitivity

```python
# Human avoidance threshold (pixels from center)
if abs(offset) < 50:  # Decrease = more sensitive
    navigation["direction"] = "STOP"
```

---

## 📞 Support

### Log Files

Backend logs go to console (stdout). To save logs:

```bash
python backend_service.py > backend.log 2>&1
```

Then view: `tail -f backend.log`

### Debug Endpoints

- **Live detection:** `http://localhost:5000/video_feed`
- **Live edges:** `http://localhost:5000/edge_visualization`
- **Health:** `http://localhost:5000/health`

### Test with cURL

```bash
# Test health
curl http://localhost:5000/health

# Test detection (requires actual image)
curl -X POST http://localhost:5000/detect \
  -H "Content-Type: application/json" \
  -d '{"image":"<base64-image-here>"}'
```

---

## 📚 References

- **YOLOv8 Docs:** https://docs.ultralytics.com/
- **Flask Documentation:** https://flask.palletsprojects.com/
- **CUDA Setup:** https://docs.nvidia.com/cuda/
- **OpenCV Edge Detection:** https://docs.opencv.org/master/da/d22/tutorial_py_canny.html

---

## 🎯 Next Steps

1. ✅ **Start backend:** `python backend_service.py`
2. ✅ **Launch Flutter app:** `flutter run`
3. ✅ **Point camera at objects** - watch detections in real-time
4. ✅ **Test navigation** - trigger door/human popups
5. ✅ **Calibrate distance** - adjust focal length for accuracy
6. ✅ **Optimize sensitivity** - adjust per-class thresholds

**Happy navigating!** 🚀
