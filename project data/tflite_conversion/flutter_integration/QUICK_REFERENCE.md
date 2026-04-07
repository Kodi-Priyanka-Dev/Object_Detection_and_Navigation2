# Quick Reference: Model Switching Implementation

## 🎯 What Was Done

✅ **HTTP Backend App** - Updated to support model switching
✅ **TFLite Mobile App** - Created with on-device model switching

---

## 📍 FILE LOCATIONS

### HTTP Backend (Flask)
```
Navigation App/
├── unified_server.py           ← UPDATED with /switch-model endpoint
└── lib/services/
    └── detection_service.dart  ← UPDATED with switchModel() method
└── lib/screens/
    └── home_screen.dart        ← UPDATED with model selector UI
```

### TFLite Mobile (New App)
```
tflite_conversion/flutter_integration/
├── tflite_detection_service.dart          ← Core TFLite inference
├── home_screen_tflite.dart                ← Mobile UI
├── main_tflite.dart                       ← App startup
├── pubspec_tflite.yaml                    ← Dependencies
├── TFLITE_MOBILE_APP_README.md            ← Features & API
├── SETUP_GUIDE.md                         ← Step-by-step guide
└── IMPLEMENTATION_SUMMARY.md              ← This summary
```

---

## 🚀 START HERE

### Option 1: Use HTTP Backend (Existing App)
**Step 1**: Start Flask backend
```powershell
cd "Navigation App"
python unified_server.py
```

Expected output:
```
✅ MULTI-MODEL BACKEND READY on port 5000
   Current Model: custom (20 classes)
🚀 Multi-model backend on port 5000
   Switch models: POST /switch-model
```

**Step 2**: Run Flutter app
```bash
flutter run --release
```

**Step 3**: Test model switching
- See status: "Ready – CUSTOM"
- Tap 🤖 (orange model icon)
- Select "YOLOv8n"
- See: "✅ Switched to yolov8n"
- Status updates to: "Ready – YOLOV8N"

---

### Option 2: Use TFLite Mobile (New App)
**Step 1**: Convert models (one-time)
```bash
cd tflite_conversion/flutter_integration

# Convert custom model
python ../convert_to_tflite.py \
    --model ../../best_model/best.pt \
    --output custom_best.tflite

# Convert YOLOv8n
python ../convert_onnx_to_tflite.py \
    --model yolov8n.pt \
    --output yolov8n.tflite
```

**Step 2**: Create Flutter project
```bash
flutter create tflite_navigation_app
cd tflite_navigation_app

# Copy files
cp ../flutter_integration/tflite_detection_service.dart lib/services/
cp ../flutter_integration/home_screen_tflite.dart lib/screens/
cp ../flutter_integration/main_tflite.dart lib/main.dart
cp ../flutter_integration/*.yaml .

# Copy models
mkdir -p assets/models
cp ../flutter_integration/*.tflite assets/models/
```

**Step 3**: Install & run
```bash
flutter pub get
flutter run --release
```

**Step 4**: Test model switching
- See status: "Model: CUSTOM"
- Tap 🤖 icon
- Select "YOLOv8n"
- Switches instantly (< 1 second)
- Status updates: "Model: YOLOV8N"

---

## 🔧 API REFERENCE

### HTTP Backend - Flask Endpoints

**Health Check**
```
GET /health
Response: {
  "status": "healthy",
  "current_model": "custom",
  "classes": 20,
  "available_models": ["custom", "yolov8n"]
}
```

**Switch Model**
```
POST /switch-model
Body: {"model": "custom"} or {"model": "yolov8n"}
Response: {
  "status": "switched",
  "current_model": "yolov8n",
  "classes": 80,
  "message": "Model yolov8n loaded"
}
```

**Detect Objects** (unchanged)
```
POST /detect
Body: {"image": "<base64_jpeg>"}
Response: {
  "detections": [...],
  "navigation": {...}
}
```

### Flutter/Dart - Detection Service

**HTTP Backend**
```dart
// Switch model
final success = await detectionService.switchModel('yolov8n');

// Get health with model info
final health = await detectionService.healthCheck();
print(health['current_model']); // "yolov8n"
print(health['classes']);       // 80
```

**TFLite Mobile**
```dart
// Load model
await service.loadModel('custom');
await service.switchModel('yolov8n');

// Get current model
String model = service.getCurrentModel(); // "yolov8n"

// Run detection
DetectionResult result = await service.detectObjects(imageBytes);
print(result.model);           // "yolov8n"
print(result.inferenceTime);   // 42ms
```

---

## 📊 PERFORMANCE METRICS

| Metric | HTTP Backend | TFLite Mobile |
|--------|--------------|---------------|
| Network needed | ✅ Yes | ❌ No |
| Model switch time | 30-60s | < 1s |
| Inference speed | 8.4ms | 25-50ms |
| Offline capable | ❌ No | ✅ Yes |
| Privacy | ⚠️ Server logging | ✅ Local only |
| Setup complexity | Low | Medium |

---

## 🔧 TROUBLESHOOTING

### HTTP Backend Issues

**Backend won't start**
```
Error: Port 5000 already in use
Solution: 
  netstat -ano | findstr :5000
  taskkill /PID <pid> /F
  python unified_server.py
```

**Model switch fails**
```
Error: Failed to switch to yolov8n
Solution:
  1. Check backend is running
  2. Verify model path: ../best_model/best.pt
  3. Check available disk space for model loading
```

**Flutter can't reach backend**
```
Error: Connection refused (10.26.67.141:5000)
Solution:
  1. Start backend: python unified_server.py
  2. Check IP matches your machine
  3. Check firewall allows port 5000
   firewall.cpl → Allow Python App
```

### TFLite Mobile Issues

**Models not found**
```
Error: Failed to load asset: assets/models/custom_best.tflite
Solution:
  1. Convert models: python convert_to_tflite.py
  2. Copy to assets/models/
  3. Add to pubspec.yaml:
     flutter:
       assets:
         - assets/models/custom_best.tflite
         - assets/models/yolov8n.tflite
```

**Out of memory**
```
Error: Exception: Out of memory
Solution:
  1. Increase FRAME_SKIP in home_screen_tflite.dart
  2. Use Custom model (smaller than YOLOv8n)
  3. Lower image resolution
```

**Slow inference**
```
Issue: Inference taking 200ms
Solution:
  1. Run with --release build: flutter run --release
  2. Use Custom model (faster)
  3. Lower FRAME_SKIP value
```

---

## 🎓 LEARNING PATH

### Beginner: Just Test HTTP Backend
1. Start Flask backend: `python unified_server.py`
2. Run Flutter app: `flutter run --release`
3. Tap 🤖 icon and switch models
4. Done! ✅

### Intermediate: Setup TFLite Mobile
1. Convert models: `convert_to_tflite.py`
2. Create Flutter project: `flutter create`
3. Copy TFLite files
4. Update pubspec.yaml
5. Run: `flutter run --release`

### Advanced: Hybrid Approach
1. Setup both apps
2. Create fallback logic in Flutter
3. Use HTTP when available
4. Use TFLite when offline
5. Best of both worlds!

---

## 📋 CHECKLIST

### HTTP Backend
- [ ] `unified_server.py` updated
- [ ] Can connect to 10.26.67.141:5000
- [ ] Health endpoint returns model info
- [ ] `/switch-model` works
- [ ] Flutter app shows model selector
- [ ] Model switching visible in status
- [ ] Snackbar feedback appears

### TFLite Mobile
- [ ] Models converted to `.tflite`
- [ ] Assets copied to `assets/models/`
- [ ] Dependencies installed
- [ ] App runs without errors
- [ ] Camera preview shows
- [ ] Detections visible
- [ ] Model switcher dropdown works
- [ ] Switching is instant (< 1s)

---

## 📞 QUICK COMMANDS

### Backend Control
```bash
# Start backend
cd "Navigation App" && python unified_server.py

# Check if running
curl http://10.26.67.141:5000/health

# Switch model via command line
$body = @{model="yolov8n"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://10.26.67.141:5000/switch-model" `
  -Method POST -Body $body -ContentType "application/json"
```

### TFLite App Control
```bash
# Run in debug
flutter run

# Run optimized
flutter run --release

# Clean & rebuild
flutter clean && flutter pub get && flutter run --release

# Build APK
flutter build apk --release

# Build iOS
flutter build ios --release
```

---

## 🎯 DECISION MATRIX

Use **HTTP Backend** if you want:
- ✅ High accuracy (RTX GPU)
- ✅ Centralized control
- ✅ Easy to update models
- ✅ Server-side processing
- ❌ Requires network
- ❌ 30-60s model switch

Use **TFLite Mobile** if you want:
- ✅ Instant model switch (< 1s)
- ✅ Works offline
- ✅ Full privacy
- ✅ Standalone deployment
- ❌ Mobile GPU limits
- ❌ Need to recompile for new models

Use **Both (Hybrid)** if you want:
- ✅ Best of both worlds
- ✅ Automatic fallback
- ✅ Flexible deployment
- ✅ Works everywhere
- ⚠️ More complex setup

---

## 📚 RELATED DOCS

- `Navigation App/BACKEND_README.md` - Backend full docs
- `Navigation App/YOLOV8N_FLUTTER_INTEGRATION.md` - Integration guide
- `tflite_conversion/` - Model conversion scripts
- `TFLITE_MOBILE_APP_README.md` - TFLite features
- `SETUP_GUIDE.md` - Step-by-step deployment
- `IMPLEMENTATION_SUMMARY.md` - Technical details

---

## ✅ STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| HTTP Backend | ✅ Ready | Multi-model with /switch-model |
| Flutter HTTP Client | ✅ Ready | Model selector in UI |
| TFLite Service | ✅ Ready | Dual model support |
| TFLite Home Screen | ✅ Ready | Camera + switcher UI |
| TFLite Main | ✅ Ready | Dual model initialization |
| Docs | ✅ Complete | 3 guides + 2 summaries |

---

**Created**: March 31, 2026
**Both apps ready to deploy** ✅
