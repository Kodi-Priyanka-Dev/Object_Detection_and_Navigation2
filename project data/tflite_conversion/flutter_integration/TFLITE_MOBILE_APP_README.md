# TFLite Mobile Navigation App with Model Switching

A Flutter-based mobile navigation application with **on-device TensorFlow Lite inference** supporting model switching between Custom and YOLOv8n models.

## 📱 Features

### Model Switching
- **Custom Model**: 20 custom indoor classes (Door, Human, Chair, Table, Sofa, Wall, etc.)
- **YOLOv8n**: 80 COCO classes (person, vehicle, furniture, animals, etc.)
- **Instant switching**: Change models on-the-fly during runtime
- **Dual model loading**: Both models pre-loaded for faster switching

### On-Device Inference
- **No network required**: All detection happens on the device
- **Fast inference**: ~30-50ms per frame depending on model
- **Optimized for mobile**: Efficient TFLite format
- **GPU support**: Leverages device GPU when available

### Navigation Features
- **Real-time detection**: Live camera stream processing
- **Detection overlays**: Shows detected objects and confidence scores
- **Model indicator**: Always know which model is active
- **Performance metrics**: Displays inference time per frame

## 📋 Project Structure

```
tflite_conversion/flutter_integration/
├── tflite_detection_service.dart       # Core TFLite inference + model switching
├── home_screen_tflite.dart            # Mobile UI with camera + model switcher
├── main_tflite.dart                   # App entry point
├── pubspec_tflite.yaml                # Dependencies
└── README.md                           # This file
```

## 🚀 Quick Start

### 1. Setup

**Convert your models to TFLite** (if not already done):
```bash
# Custom model conversion
python convert_to_tflite.py --model ../best_model/best.pt --output custom_best.tflite

# YOLOv8n conversion
python convert_onnx_to_tflite.py --model yolov8n.pt --output yolov8n.tflite
```

### 2. Create Asset Structure
```
flutter_project/
├── assets/
│   └── models/
│       ├── custom_best.tflite         (20 classes)
│       └── yolov8n.tflite             (80 classes)
├── lib/
│   ├── main.dart                      (copy from main_tflite.dart)
│   ├── services/
│   │   └── tflite_detection_service.dart
│   └── screens/
│       └── home_screen.dart            (copy from home_screen_tflite.dart)
└── pubspec.yaml                        (use pubspec_tflite.yaml as reference)
```

### 3. Install Dependencies
```bash
flutter pub get
```

### 4. Run the App
```bash
# Development
flutter run

# Release (optimized)
flutter run --release
```

## 🎯 Model Switching

### How It Works

**At Startup:**
1. Custom model loads (default) → ready for detection
2. YOLOv8n pre-loads in background → instant switching

**During Runtime:**
1. Tap the **orange model icon** at the bottom
2. Select from dropdown:
   - ✓ Custom Model (20 classes) - *Indoor specialized*
   - ✓ YOLOv8n (80 classes) - *General purpose*
3. Model switches instantly
4. Feedback snackbar confirms switch

### Performance Comparison

| Metric | Custom | YOLOv8n |
|--------|--------|---------|
| Classes | 20 (indoor) | 80 (general) |
| Input Size | 416x416 | 640x640 |
| Inference Time | ~25ms | ~40ms |
| Model Size | ~15MB | ~6MB |
| Best For | Navigation | General detection |

## 📊 API Reference

### TFLiteDetectionService

```dart
// Load a model
await service.loadModel('custom');
await service.loadModel('yolov8n');

// Switch models dynamically
final success = await service.switchModel('yolov8n');

// Get current model
String current = service.getCurrentModel();  // Returns: 'custom' or 'yolov8n'

// Run detection
DetectionResult result = await service.detectObjects(imageBytes);

// Cleanup
service.dispose();
```

### DetectionResult

```dart
class DetectionResult {
  List<Detection> detections;      // Detected objects
  int inferenceTime;               // Time in milliseconds
  String model;                    // Currently active model
}

class Detection {
  double x, y;                     // Center position (normalized 0-1)
  double width, height;            // Bounding box size
  double confidence;               // Confidence score (0-1)
  String classLabel;               // Object class name
}
```

## 🔧 Customization

### Change Default Model
Edit `main_tflite.dart`:
```dart
// Change this line:
await detectionService.loadModel('custom');

// To:
await detectionService.loadModel('yolov8n');
```

### Adjust Confidence Threshold
Edit `tflite_detection_service.dart`:
```dart
if (confidence > 0.35) {  // Change from 0.35 to your threshold
  detections.add(Detection(...));
}
```

### Add Custom Classes
Update class labels in `tflite_detection_service.dart`:
```dart
'custom': [
  'your_class_1',
  'your_class_2',
  // ... more classes
],
```

### Adjust Processing Speed
Edit `home_screen_tflite.dart`:
```dart
static const int FRAME_SKIP = 3;  // Process every 3rd frame
// Lower = faster but uses more resources
// Higher = slower processing but less battery
```

## 📱 Mobile Deployment

### Android
```bash
flutter build apk --release
# or for App Bundle:
flutter build appbundle --release
```

### iOS
```bash
flutter build ios --release
```

## ⚡ Performance Tips

1. **Use Release Mode**: Always test with `flutter run --release`
2. **Lower Frame Skip**: Reduce `FRAME_SKIP` for faster detection but more CPU
3. **GPU Delegation**: TFLite automatically uses GPU on supported devices
4. **Model Selection**: 
   - Custom model for indoor navigation (faster)
   - YOLOv8n for general object detection (more versatile)

## 🐛 Troubleshooting

### Model Not Found
```
Error: Assets file not found - custom_best.tflite
```
**Solution**: Ensure models are in `assets/models/` and listed in `pubspec.yaml`

### Interpreter Error
```
Error: Failed to load model: Invalid model file
```
**Solution**: Convert models properly using `convert_to_tflite.py` or `convert_onnx_to_tflite.py`

### Out of Memory
```
Exception: Out of memory
```
**Solution**: 
- Increase `FRAME_SKIP` to skip more frames
- Lower input resolution if possible
- Close other apps

### Slow Inference
```
Inference: 200ms (too slow)
```
**Solution**:
- Use Custom model instead of YOLOv8n
- Enable GPU delegation in interpreter
- Reduce image resolution

## 📚 Integration with Backend

If you want to combine with the Flask backend server:

```dart
// Use both HTTP backend and TFLite
class HybridDetectionService {
  final TFLiteDetectionService tflite;
  final DetectionService http;  // From main app
  
  Future<DetectionResult> detectWithFallback(Uint8List image) async {
    try {
      // Try HTTP first (if connected)
      final httpResult = await http.detectObjects(image);
      return httpResult;
    } catch (e) {
      // Fallback to local TFLite
      return await tflite.detectObjects(image);
    }
  }
}
```

## 🔐 Privacy & Offline

- **100% On-Device**: All processing happens locally
- **No Network Required**: Works completely offline
- **No Data Transmission**: Zero phone home, zero tracking
- **Privacy Focused**: Perfect for sensitive environments

## 📖 Files Reference

| File | Purpose |
|------|---------|
| `tflite_detection_service.dart` | TFLite inference engine |
| `home_screen_tflite.dart` | Mobile UI screen |
| `main_tflite.dart` | App initialization |
| `pubspec_tflite.yaml` | Dependencies |

## 🤝 Support

### Converting Models to TFLite
See: `../convert_to_tflite.py` and `../convert_onnx_to_tflite.py`

### Android-specific Issues
Check TFLite Documentation: https://www.tensorflow.org/lite/guide

### iOS-specific Issues
Check iOS Pod Setup: https://pub.dev/packages/tflite_flutter

## ✅ Checklist

- [ ] Models converted to `.tflite` format
- [ ] Assets placed in `assets/models/`
- [ ] Dependencies installed (`flutter pub get`)
- [ ] Tested on device (`flutter run --release`)
- [ ] Model switching works (tap orange icon)
- [ ] Detections visible on screen
- [ ] Inference time is acceptable

## 📝 Notes

- TFLite models must be `.tflite` format
- Input sizes: Custom=416x416, YOLOv8n=640x640
- Both models pre-loaded at startup for instant switching
- Models consume ~20-25MB RAM total
- Inference is CPU+GPU (automatically optimized)

---

**Last Updated**: March 2026
**TFLite Version**: 0.10+
**Flutter Version**: 3.0+
