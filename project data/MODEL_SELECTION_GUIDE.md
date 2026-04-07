# YOLOv8n vs YOLOv8l - Model Selection Guide

## 📊 Quick Comparison

| Feature | YOLOv8n (Nano) | YOLOv8l (Large) |
|---------|---|---|
| **Model Size** | 6.3 MB | 83 MB |
| **Inference Speed** | 5-10 ms/frame | 30-50 ms/frame |
| **Accuracy** | Baseline | +6-8% better |
| **GPU Memory** | ~500 MB | 8-10 GB |
| **Parameters** | 3.3M | 43.7M |
| **Training Time** | 30-60 min | 2-4 hours |
| **Best For** | Real-time, edge devices | Accuracy-critical tasks |

---

## 🎯 When to Use Which Model

### Choose **YOLOv8n** (Nano) if:
✅ You need **real-time detection** (mobile app, webcam)  
✅ **Speed is critical** (interactive features)  
✅ **GPU memory is limited** (< 2GB)  
✅ You want **fast training** (< 1 hour)  
✅ **Model size matters** (mobile deployment)  
✅ Running on **edge devices** (Jetson, RPi)  

### Choose **YOLOv8l** (Large) if:
✅ You need **maximum accuracy** (critical detections)  
✅ **Processing time is not critical** (batch processing)  
✅ You have **plenty of GPU memory** (12GB+)  
✅ **Training time is acceptable** (2-4 hours)  
✅ Running on **powerful servers** (RTX A2000, RTX 3090)  
✅ Offline processing is **acceptable** (not real-time)  

---

## 📋 Training Both Models

### **Step 1: Train YOLOv8n (Fast)**

```bash
cd "c:\Users\Priyanka\Documents\project data"
python train3.py
```

**Output:**
```
Models saved:
  - runs/detect_yolov8n/weights/best.pt
  - best_model/best_nano.pt (copied automatically)
```

**Duration:** 30-60 minutes with GPU

---

### **Step 2: Train YOLOv8l (Accurate)**

```bash
cd "c:\Users\Priyanka\Documents\project data"
python train_yolov8l.py
```

**Output:**
```
Models saved:
  - runs/detect_yolov8l/weights/best.pt
  - best_model/best_large.pt (copied automatically)
```

**Duration:** 2-4 hours with GPU

---

## 🚀 Switching Between Models

### **Method 1: Environment Variable (Recommended)**

#### Use YOLOv8n (Nano - Default)
```bash
# On Windows, no need to set - default is "nano"
cd "Navigation App"
python backend_service.py
```

#### Use YOLOv8l (Large - Better Accuracy)
```bash
# Set environment variable
set MODEL_TYPE=large

# Then start backend
cd "Navigation App"
python backend_service.py
```

**Output will show:**
```
[4/4] Loading YOLOv8L model...
      🎯 Using YOLOv8L fine-tuned model for all detections
      📌 Variant: large (set via MODEL_TYPE environment variable)

  📦 YOLOv8L Model: ..\ best_model\best_large.pt (exists: True)
      ✅ YOLOv8L model loaded (20 classes)

============================================================
✅ BACKEND READY - YOLOv8L model loaded on port 5000
```

---

### **Method 2: Command Line (Persistent in Current Session)**

```bash
# For YOLOv8n (Nano)
cmd /c "cd Navigation App && python backend_service.py"

# For YOLOv8l (Large)
cmd /c "set MODEL_TYPE=large && cd Navigation App && python backend_service.py"
```

---

### **Method 3: Permanent (Registry - Windows)**

```bash
# Set permanently (for all future sessions)
setx MODEL_TYPE large

# Then close and reopen terminal
```

---

## 📱 Running Flutter App with Different Models

### **With YOLOv8n (Nano - Fast)**
```bash
# Terminal 1: Start YOLOv8n backend
cd "Navigation App"
python backend_service.py

# Terminal 2: Run Flutter with YOLOv8n
flutter run --dart-define=BACKEND_IP=192.168.x.x --dart-define=BACKEND_PORT=5000
```

**Expected Performance:**
- Inference: 5-10 ms per frame
- Frame rate: ~100 FPS (real-time)
- Responsive UI

---

### **With YOLOv8l (Large - Accurate)**
```bash
# Terminal 1: Start YOLOv8l backend
set MODEL_TYPE=large
cd "Navigation App"
python backend_service.py

# Terminal 2: Run Flutter (same command)
flutter run --dart-define=BACKEND_IP=192.168.x.x --dart-define=BACKEND_PORT=5000
```

**Expected Performance:**
- Inference: 30-50 ms per frame
- Frame rate: ~20-30 FPS (slower but more accurate)
- Better detection accuracy

---

## 📂 File Structure

```
project_data/
├── best_model/
│   ├── best_nano.pt          # YOLOv8n trained model (6.3 MB)
│   ├── best_large.pt         # YOLOv8l trained model (83 MB)
│   └── best.pt               # Symlink/copy to currently used model
│
├── train3.py                 # Train YOLOv8n
├── train_yolov8l.py          # Train YOLOv8l
│
├── Navigation App/
│   ├── backend_service.py    # Backend that loads model based on MODEL_TYPE
│   └── ...
```

---

## ⚙️ Code Changes in Backend

### How it Works

**File:** `backend_service.py` (Lines 47-65)

```python
# SELECT MODEL TYPE (nano for speed, large for accuracy)
MODEL_TYPE = os.getenv("MODEL_TYPE", "nano").lower()

# Model paths for different variants
MODEL_PATHS = {
    "nano": os.path.join("..", "best_model", "best_nano.pt"),
    "large": os.path.join("..", "best_model", "best_large.pt"),
}

CUSTOM_MODEL_PATH = MODEL_PATHS.get(MODEL_TYPE, MODEL_PATHS["nano"])
MODEL_VARIANT = MODEL_TYPE.upper()  # For logging: "NANO" or "LARGE"
```

---

## 🔄 Switching Models Mid-Session

### Option A: Stop Backend, Switch, Restart

```bash
# Terminal 1 (where backend is running)
Press Ctrl+C to stop

# Then:
set MODEL_TYPE=large
python backend_service.py
```

### Option B: Keep Both Backends Running (Different Ports)

```bash
# Terminal 1: NanoBackend on port 5000
python backend_service.py

# Terminal 2: Large model on different port (requires code change)
set MODEL_TYPE=large
python backend_service.py  # Would need different port config
```

---

## 📊 Performance Metrics

### YOLOv8n Performance
```
Inference Time: 5-10 ms per frame
Memory Usage: 500 MB GPU
Model Setup Time: ~2 seconds
Throughput: 100+ FPS single frame

Accuracy on Test Set:
  mAP50: 0.85 (typical)
  mAP75: 0.78 (typical)
```

### YOLOv8l Performance
```
Inference Time: 30-50 ms per frame
Memory Usage: 8-10 GB GPU
Model Setup Time: ~5-10 seconds
Throughput: 20-30 FPS single frame

Accuracy on Test Set:
  mAP50: 0.92 (typical, ~6-8% better)
  mAP75: 0.86 (typical)
```

---

## 🎯 Use Cases

### YOLOv8n Best For:
- 📱 Mobile navigation app (real-time)
- 🎥 Live webcam streaming
- 📡 Edge devices (Jetson Nano, RPI)
- 🚗 Autonomous vehicles (need low latency)
- ⚡ Interactive features

### YOLOv8l Best For:
- 📹 Video processing (batch)
- 🔍 Security surveillance (accuracy matters)
- 📊 Data analysis
- 🏭 Industrial inspection
- 💼 Enterprise systems

---

## ✅ Troubleshooting

### Problem: "YOLOv8l model not found"

**Solution:**
```bash
# Make sure you trained it first
python train_yolov8l.py

# Verify file exists
dir best_model  # Should show best_large.pt

# Check file size (should be ~83 MB)
```

---

### Problem: "Out of memory" error with YOLOv8l

**Solution 1 - Reduce batch size:**
```python
# In train_yolov8l.py, line ~91
"batch": 4,  # Reduce from 8 to 4
```

**Solution 2 - Use YOLOv8n instead:**
```bash
python train3.py
```

**Solution 3 - Use medium model (YOLOv8m):**
```python
# Create similar to train_yolov8l.py but use yolov8m.pt
model = YOLO("yolov8m.pt")
```

---

### Problem: "MODEL_TYPE environment variable not working"

**Solution:**
```bash
# Verify it's set
echo %MODEL_TYPE%

# Set it explicitly in same command window
set MODEL_TYPE=large && python backend_service.py

# Or set it permanently
setx MODEL_TYPE large  # Then restart terminal
```

---

## 📈 Model Size Hierarchy

```
YOLOv8n (Nano)   →  6.3 MB  →  Fastest, least accurate
YOLOv8s (Small)  → 22 MB    →  
YOLOv8m (Medium) → 49 MB    →  
YOLOv8l (Large)  → 83 MB    →  
YOLOv8x (XL)     → 130 MB   →  Slowest, most accurate
```

---

## 🎓 Next Steps

1. **Train YOLOv8n first** (faster to experiment)
   ```bash
   python train3.py
   ```

2. **Test with Flutter app** (verify detection works)
   ```bash
   flutter run --dart-define=BACKEND_IP=192.168.x.x
   ```

3. **If accuracy not good enough, train YOLOv8l** (better results)
   ```bash
   python train_yolov8l.py
   ```

4. **Switch models and compare** (set MODEL_TYPE=large)

5. **Choose the best balance** for your use case

---

## 📖 Summary

**Quick Reference:**

| Task | Command |
|------|---------|
| Train YOLOv8n | `python train3.py` |
| Train YOLOv8l | `python train_yolov8l.py` |
| Start nano backend | `python backend_service.py` |
| Start large backend | `set MODEL_TYPE=large && python backend_service.py` |
| List models | `dir best_model` |
| Check model size | `dir best_model /s` |
| Remove large model | `del best_model\best_large.pt` |

---

**Choose wisely! Both models are powerful, just optimized for different needs.** 🚀
