# Quick Start Checklist — Get Running in 5 Minutes

## ⚡ Fastest Path: Test Backend + HTTP Mobile App

### Step 1: Prepare Backend (2 minutes)

```powershell
# Navigate to Navigation App folder
cd "C:\Users\Priyanka\Desktop\ai project\project data\Navigation App"

# Verify custom model exists
Test-Path ".\best_model\best.pt"
# Should return: True

# Install dependencies (if not already done)
pip install flask ultralytics torch opencv-python
```

### Step 2: Start Backend Server (1 minute)

```powershell
# Terminal 1 - Start Flask server
python unified_server.py

# Expected output:
# * Running on http://127.0.0.1:5000
# ✓ HumanDetectionModel loaded
```

### Step 3: Test Backend (1 minute)

```powershell
# Terminal 2 - In same folder
curl http://localhost:5000/health

# Expected:
# {"status": "healthy", "current_model": "custom", "available_models": ["custom", "yolov8n"], ...}
```

✅ **Backend is working!**

---

### Step 4: Prepare Flutter App (1 minute)

```bash
# Terminal 3 - Navigate to Flutter project
cd "C:\Users\Priyanka\Desktop\ai project\project data\Navigation App"

# Clean and prepare
flutter clean
flutter pub get
```

### Step 5: Update Backend URL

**File**: `lib/services/detection_service.dart`

Find line with:
```dart
static const String apiUrl = 'http://192.168.x.x:5000';
```

Replace with:
```dart
static const String apiUrl = 'http://localhost:5000';  // For emulator
// OR
static const String apiUrl = 'http://YOUR_COMPUTER_IP:5000';  // For physical device
```

To find your computer IP:
```powershell
ipconfig  # Look for "IPv4 Address" under your network adapter
# Typically: 192.168.x.x or 10.0.x.x
```

### Step 6: Run App

```bash
flutter run --release
```

Expected output:
```
✓ Built successfully
✓ Launching lib/main.dart on Android Emulator
```

---

### Step 7: Test Model Switching ✅

1. **App opens** → camera feed shows
2. **Status bar** shows "Ready – CUSTOM"
3. **Tap 🤖 icon** (top-right) → dropdown appears
4. **Select "YOLOV8N"** → status changes to "Ready – YOLOV8N"
5. **Tap again** to switch back

**If it fails**:
- Check Flask server is still running (Terminal 1)
- Check backend URL is correct (detection_service.dart)
- Check firewall isn't blocking port 5000

---

## 📊 If You Want Statistics

### Quick Test with Python Scripts

```powershell
cd "C:\Users\Priyanka\Desktop\ai project\project data"

# Install if needed
pip install ultralytics opencv-python

# Test detection on a single image
python -c "
from yolov8n_scripts_improved import detect_objects_in_image
detect_objects_in_image('your_test_image.jpg')
"
```

Expected output:
```
==================================================
  HUMANS (priority): 2 detected
==================================================
  ★ person  | conf: 0.892 | box: (100, 150, 250, 500)

  OTHER TARGET CLASSES: 3 detected
--------------------------------------------------
  [Electronics  ] laptop         | conf: 0.812
  [Furniture    ] chair          | conf: 0.756
```

---

## 🚀 For Offline Operation (TFLite)

**If you want the app to work without the server:**

1. Convert models to TFLite:
   ```bash
   python tflite_conversion/convert_to_tflite.py
   ```

2. Copy files to Flutter assets:
   ```
   tflite_conversion/flutter_integration/assets/models/
     ├── custom_model.tflite
     └── yolov8n.tflite
   ```

3. Use TFLite app instead:
   ```bash
   cd tflite_conversion/flutter_integration/
   flutter run --release
   ```

**Advantage**: Works without server, instant model switching
**Disadvantage**: Slower on mobile, larger app size

---

## 📋 Verification Checklist

- [ ] `best_model/best.pt` exists
- [ ] Flask server starts without errors
- [ ] `/health` endpoint responds
- [ ] `/switch-model` endpoint works
- [ ] Flutter app starts
- [ ] 🤖 icon appears in top-right
- [ ] Model dropdown opens
- [ ] Model switch works (status bar updates)
- [ ] Detection shows new model's results

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Flask won't start | Check `best_model/best.pt` exists |
| `/health` fails | Make sure no other app using port 5000 |
| App won't connect | Check backend URL in detection_service.dart |
| 🤖 icon missing | Make sure you're on home_screen.dart (not debug screen) |
| Model switch fails | Check Flutter logs: `flutter run -v` |
| "YOLOv8n missing" | Backend will auto-download, give it 30 seconds |

---

## 📁 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `Navigation App/unified_server.py` | Flask server | ✅ Ready |
| `Navigation App/lib/services/detection_service.dart` | HTTP client | ✅ Ready |
| `Navigation App/lib/screens/home_screen.dart` | UI with model switcher | ✅ Ready |
| `yolov8n_scripts_improved.py` | Detection scripts | ✅ Ready |

---

## 📚 Documentation

For more details, see:
- **YOLOV8N_SCRIPTS_REFERENCE.md** — How to use detection scripts
- **COMPLETE_INTEGRATION_GUIDE.md** — Full architecture & deployment
- **MODEL_SWITCHING_IMPROVEMENTS.md** — Technical improvements

---

## ✅ Success Indicators

You know it's working when:

1. **Backend** → Flask server running on port 5000
2. **Health check** → `/health` returns model status
3. **App** → Flutter app shows camera feed
4. **UI** → 🤖 icon visible in top-right
5. **Switch** → Tapping icon switches between "CUSTOM" and "YOLOV8N"
6. **Detection** → Detection results change with model

---

## 🎯 Next Steps After Getting It Working

1. **Test with real camera** — Use actual webcam instead of emulator camera
2. **Optimize inference** — Adjust confidence threshold in `home_screen.dart`
3. **Deploy to device** — Build release APK and install on Android device
4. **Collect metrics** — Use ObjectAnalyzer to gather detection statistics
5. **Fine-tune** — Retrain custom model if needed (`retrain_18class.py`)

---

## 💡 Pro Tips

**Faster development**:
```bash
# Use debug mode with hot reload
flutter run  # (not --release)
# Change code, save file → instant reload
```

**Check logs**:
```bash
# See detailed Flask/app output
flutter run -v  # Verbose logging
```

**Test model switching in code**:
```python
# In Python, test the endpoint
import requests
url = "http://localhost:5000/switch-model"
data = {"model": "yolov8n"}
r = requests.post(url, json=data)
print(r.json())
```

---

**Ready? Start with Step 1! ⚡**

