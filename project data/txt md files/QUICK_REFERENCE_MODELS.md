# ⚡ Quick Reference: YOLOv8n vs YOLOv8l

## 🚀 30-Second Summary

**YOLOv8n (Nano):** Fast + Small = Real-time detection ⚡  
**YOLOv8l (Large):** Slow + Accurate = Best detection 🎯

---

## 📋 Training Commands

### Train YOLOv8n (30-60 minutes)
```bash
cd "c:\Users\Priyanka\Documents\project data"
python train3.py
# Output: best_model/best_nano.pt (6.3 MB)
```

### Train YOLOv8l (2-4 hours)
```bash
cd "c:\Users\Priyanka\Documents\project data"
python train_yolov8l.py
# Output: best_model/best_large.pt (83 MB)
```

---

## 🔄 Switching Models (3 Ways)

### **Way 1: Use Environment Variable (Easiest)**

#### Switch to YOLOv8n (Nano - Default)
```bash
# Optional (nano is default anyway)
set MODEL_TYPE=nano
cd Navigation App
python backend_service.py
```

#### Switch to YOLOv8l (Large - Accurate)
```bash
set MODEL_TYPE=large
cd Navigation App
python backend_service.py
```

---

### **Way 2: Single Command**

```bash
# YOLOv8n
cd Navigation App && python backend_service.py

# YOLOv8l
set MODEL_TYPE=large && cd Navigation App && python backend_service.py
```

---

### **Way 3: PowerShell (Windows)**

```powershell
# YOLOv8n (Nano)
$env:MODEL_TYPE="nano"; cd "Navigation App"; python backend_service.py

# YOLOv8l (Large)
$env:MODEL_TYPE="large"; cd "Navigation App"; python backend_service.py
```

---

## 📱 Running Flutter App

**Same for both models!**
```bash
flutter run --dart-define=BACKEND_IP=192.168.x.x --dart-define=BACKEND_PORT=5000
```

Just switch the backend model using steps above, then app will use that model.

---

## 📊 Performance Comparison

```
                YOLOv8n    YOLOv8l
Speed:          ⚡⚡⚡     ⚡
Accuracy:       ⭐⭐⭐    ⭐⭐⭐⭐⭐
Size:           6 MB       83 MB
Memory:         0.5 GB     8 GB
Inference:      5-10 ms    30-50 ms
FPS:            100+       20-30
```

---

## ✅ Verification

### Check Model Loaded Successfully

Look for in backend output:
```
✅ YOLOv8N model loaded (20 classes)
or
✅ YOLOv8L model loaded (20 classes)
```

### Check Model File Exists
```bash
dir best_model

# You should see:
# - best_nano.pt  (if you trained YOLOv8n)
# - best_large.pt (if you trained YOLOv8l)
```

---

## ⚠️ Common Issues

### "Model not found"
Solution: Train it first!
```bash
# For nano:
python train3.py

# For large:
python train_yolov8l.py
```

### "Out of memory" (YOLOv8l only)
Solutions:
1. Reduce batch size in `train_yolov8l.py`: `"batch": 4`
2. Use YOLOv8n instead (less memory)
3. Use YOLOv8m (medium) – 49 MB

### "MODEL_TYPE not working"
Solution:
```bash
# Verify it's set
echo %MODEL_TYPE%

# Set in same command:
set MODEL_TYPE=large && cd Navigation App && python backend_service.py

# Or set permanently:
setx MODEL_TYPE large
# Then restart terminal/CMD
```

---

## 🎯 Which One to Use?

**Choose YOLOv8n if:**
- ✅ Need real-time detection
- ✅ Using mobile app
- ✅ GPU memory < 2 GB
- ✅ Speed > Accuracy

**Choose YOLOv8l if:**
- ✅ Need maximum accuracy
- ✅ Batch processing (offline)
- ✅ GPU memory > 12 GB
- ✅ Accuracy > Speed

---

## 📋 File Locations

```
best_model/
├── best_nano.pt          (6.3 MB) ← YOLOv8n
├── best_large.pt         (83 MB)  ← YOLOv8l
└── best.pt               <- Legacy (symlink)

runs/
├── detect_yolov8n/       ← YOLOv8n training results
└── detect_yolov8l/       ← YOLOv8l training results
```

---

## 🚀 Quick Start (Two Models)

**Terminal 1: Train YOLOv8n**
```bash
python train3.py
# ~60 minutes
```

**Terminal 2: Train YOLOv8l** (while nano trains, optional)
```bash
python train_yolov8l.py
# ~3 hours
```

**Test YOLOv8n:**
```bash
set MODEL_TYPE=nano
cd Navigation App
python backend_service.py
# In another terminal:
flutter run --dart-define=BACKEND_IP=192.168.x.x
```

**Switch to YOLOv8l:**
```bash
# Stop backend (Ctrl+C)
set MODEL_TYPE=large
python backend_service.py
# App automatically uses YOLOv8l now
```

---

## 📞 Support

| Issue | Check |
|-------|-------|
| Model not loading | `dir best_model` (file exists?) |
| Wrong model used | `echo %MODEL_TYPE%` (shows "nano" or "large"?) |
| Slow detection | `set MODEL_TYPE=nano` (use faster model) |
| Poor accuracy | `set MODEL_TYPE=large` (use accurate model) |
| Out of memory | Use YOLOv8n instead or reduce batch size |

---

## 💡 Pro Tips

1. **Start with YOLOv8n** (faster to test)
2. **If accuracy not good**, switch to YOLOv8l
3. **Keep both trained** for flexibility
4. **YOLOv8l for production**, YOLOv8n for development
5. **Use `set MODEL_TYPE=xyz`** to switch instantly

---

**Remember:** YOLOv8n = Speed 🏃  |  YOLOv8l = Accuracy 🎯
