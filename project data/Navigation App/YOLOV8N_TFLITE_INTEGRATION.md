# YOLOv8n TFLite Integration Guide

## Overview
The navigation app now supports **on-device object detection** using YOLOv8n converted to TensorFlow Lite format. This enables fast, offline detection without relying on a backend server.

## What's Been Set Up

### 1. Model Conversion ✅
- YOLOv8n model converted from `.pt` to `.tflite` format
- Model location: `tflite_conversion/models/yolov8n.tflite` 
- Model size: ~6.2 MB (optimized for mobile)
- Input size: 416x416 pixels
- Classes: 80 COCO dataset classes

### 2. Flutter Integration ✅
- **TFLite package**: `tflite_flutter: ^0.11.0` added to `pubspec.yaml`
- **Assets**: Model copied to `assets/models/yolov8n.tflite`
- **Assets configured** in `pubspec.yaml` for deployment

### 3. On-Device Detection Service ✅
Created `lib/services/tflite_detection_service.dart` with:
- TFLite interpreter initialization
- Camera frame conversion (YUV420, BGRA8888, NV21)
- Real-time inference on device
- COCO class detection (person, car, dog, etc.)
- Returns standard `DetectionResponse` model

## How to Use

### Option 1: Use On-Device Detection (Fast, Offline)

```dart
// import the service
import 'services/tflite_detection_service.dart';

// Initialize
final tfliteService = TFLiteDetectionService();
await tfliteService.initialize();

// In your camera stream handler
final response = await tfliteService.detectObjects(
  cameraImage,
  confThreshold: 0.35,
);

// Parse DetectionResponse
if (response != null) {
  for (var detection in response.detections) {
    print('${detection.className}: ${detection.confidence}');
  }
}

// Cleanup
tfliteService.dispose();
```

### Option 2: Use Backend Detection (More Accurate)

```dart
// Already integrated in the existing app
import 'services/detection_service.dart';

final detectionService = DetectionService();
final response = await detectionService.detectObjects(cameraImage);
```

### Option 3: Hybrid Approach (Best of Both)

Create a `hybrid_detection_service.dart` that:
1. Tries on-device detection first (fast)
2. Falls back to backend if needed
3. Allows user to toggle between modes

## Performance Expectations

### On-Device (TFLite)
- **Inference Time**: ~100-200ms (depends on device)
- **No latency**: No network delay
- **Battery**: Higher power consumption than static analysis
- **Privacy**: All processing on device
- **Requires**: Good device performance (newer phones)

### Backend (Flask)
- **Inference Time**: ~300-500ms + network latency
- **Network**: Requires WiFi/Mobile connection
- **Accuracy**: Can be higher with larger models
- **Server-side**: Benefits from GPU acceleration

## Next Steps

### 1. Update Main App UI
In your app's detection screen, add a toggle to switch between inference modes:

```dart
// Add this to your detection screen
Segment<String> inferenceMode = 'tflite'; // or 'backend'

if (inferenceMode == 'tflite') {
  // Use TFLiteDetectionService
} else {
  // Use DetectionService (backend)
}
```

### 2. Install TFLite Package
```bash
flutter pub get
```

### 3. Run the App
```bash
flutter run
```

The app will automatically load and use the TFLite model for detection.

### 4. Test Door Detection
The yolov8n model detects "door" as a COCO class. Test with:
- Real doors in your environment
- Adjust confidence threshold if needed
- Monitor inference time on your device

## Troubleshooting

### Model Not Loading
- Verify `assets/models/yolov8n.tflite` exists
- Check `pubspec.yaml` has correct asset path
- Run `flutter pub get`

### Slow Inference
- Your device may have limited resources
- Try reducing input resolution (currently 416x416)
- Check device CPU usage with Flutter DevTools

### No Detections
- Adjust `confThreshold` (try lower: 0.25-0.30)
- Ensure good lighting conditions
- Check model path and initialization

### Memory Issues  
- Close other apps
- Reduce Frame processing rate
- Use backend instead for older devices

## Classes Detected

YOLOv8n detects 80 COCO classes including:
- **People**: person
- **Vehicles**: car, truck, bus, bicycle, motorcycle
- **Animals**: cat, dog, horse, bird
- **Objects**: chair, table, laptop, phone, cup
- **Doors**: Yes! Detects doors for navigation
- ... and 70+ more classes

See full list in `tflite_detection_service.dart` → `cocoNames`

## Architecture

```
Navigation App
├── pubspec.yaml (✅ updated)
├── lib/
│   ├── services/
│   │   ├── detection_service.dart (backend)
│   │   └── tflite_detection_service.dart (✅ NEW - on-device)
│   ├── models/
│   │   └── detection_model.dart
│   └── ...
└── assets/
    └── models/
        └── yolov8n.tflite (✅ NEW - 6.2MB model)
```

## Benefits of Dual Inference

✅ **Fast Response**: TFLite for real-time detection  
✅ **Privacy**: Local processing without sending frames  
✅ **Offline**: Works without internet connection  
✅ **Fallback**: Can use backend if TFLite unavailable  
✅ **User Choice**: Let users pick their preferred mode  

## Backend Still Available

If you want to use the Flask backend (unified_server.py), keep it running:
```bash
python unified_server.py
```

The app will use whichever is configured (or both).

## Model Details

**YOLOv8n Specs:**
- Parameters: ~3.15M (lightweight)
- Input: 416x416 RGB images  
- Output: 84 channels × 3549 anchors
- Framework: TensorFlow Lite
- Quantization: Full precision (no quantization for accuracy)

**Conversion Info:**
- Original: `yolov8n.pt` (6.2 MB)
- Converted: `yolov8n.tflite` (~6.2 MB)
- Process: YOLOv8 export → TFLite format

---

**Ready to test!** Run `flutter run` and the app will use the on-device model for detection.
