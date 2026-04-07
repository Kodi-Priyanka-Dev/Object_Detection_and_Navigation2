# TFLite Model Conversion & Mobile Deployment

Complete guide for converting YOLOv8 `.pt` models to `.tflite` format for deployment on Flutter mobile apps.

## 📋 Overview

This folder contains an end-to-end pipeline for:
- Converting trained YOLOv8 models from PyTorch format to TensorFlow Lite
- Testing converted models for accuracy and performance
- Generating Flutter integration code and setup guides

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Convert Model

```bash
python convert_to_tflite.py
```

**Output:** `models/best.tflite` (~5-15 MB)

### 3. Test Model

```bash
python test_tflite.py
```

### 4. Generate Flutter Code

```bash
python flutter_integration_generator.py
```

---

## 📁 File Structure

```
tflite_conversion/
├── convert_to_tflite.py              # Main conversion script
├── test_tflite.py                    # Model testing & validation
├── flutter_integration_generator.py  # Flutter code generator
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── models/                           # Output directory
│   └── best.tflite                   # Converted model (generated)
└── flutter_integration/              # Generated Flutter files (generated)
    ├── tflite_detection_service.dart
    ├── pubspec_updates.txt
    ├── main_dart_template.dart
    └── assets_structure.txt
```

---

## 🔄 Conversion Pipeline

### Step 1: Load & Export

The `convert_to_tflite.py` script:
- Loads your trained YOLOv8 model from `../best_model/best.pt`
- Exports through intermediate ONNX format
- Converts to TensorFlow Lite optimized for mobile

```python
python convert_to_tflite.py
```

**Configuration options in script:**
- `IMG_SIZE`: Input resolution (default: 416)
- `quantize`: Enable int8 quantization (default: True)
- `dynamic`: Fixed vs dynamic input shapes

### Step 2: Validate

```python
python test_tflite.py
```

Tests include:
- Model loading verification
- Inference on sample images
- Performance metrics (inference time, FPS)
- Output shape validation

**Expected Output:**
```
✓ Model loaded successfully
✓ test_image_01.jpg → 45.2ms
✓ test_image_02.jpg → 43.8ms
Average inference time: 44.5ms
FPS (estimated): 22.5
```

### Step 3: Generate Flutter Code

```python
python flutter_integration_generator.py
```

Generates:
- `tflite_detection_service.dart` - Wrapper for model inference
- `pubspec_updates.txt` - Required dependencies
- `main_dart_template.dart` - App initialization template
- `assets_structure.txt` - Asset folder organization

---

## 📱 Flutter Integration

### Copy Generated Files

1. **Detection Service**
   ```
   Navigation App/lib/services/tflite_detection_service.dart
   ← Copy from flutter_integration/tflite_detection_service.dart
   ```

2. **Model Assets**
   ```
   Navigation App/assets/models/best.tflite
   ← Copy from models/best.tflite
   ```

### Update Dependencies

Edit `Navigation App/pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  tflite_flutter: ^0.10.0
  camera: ^0.10.5
  image: ^4.0.0
  permission_handler: ^11.4.0
```

Install: `flutter pub get`

### Update pubspec.yaml Assets Section

```yaml
flutter:
  assets:
    - assets/models/best.tflite
```

### Initialize in main.dart

```dart
import 'services/tflite_detection_service.dart';

void main() async {
  final detectionService = TFLiteDetectionService();
  await detectionService.loadModel();
  runApp(MyApp(detectionService: detectionService));
}
```

---

## ⚡ Key Benefits

| Feature | Benefit |
|---------|---------|
| **On-Device** | No network latency, real-time inference |
| **Privacy** | Camera frames never leave device |
| **Offline** | Works without internet connection |
| **Smaller** | 3-10× smaller than original model |
| **Power** | Lower battery consumption |
| **Performance** | 20-60 FPS on modern phones |

---

## 📊 Model Specifications

### Input
- **Format**: RGB image tensor
- **Size**: 416×416 (configurable)
- **Type**: Float32, normalized [0, 1]

### Output
- **Predictions**: 25200×25 tensor (YOLOv8 format)
- **Interpretation**: 
  - First 4 values: bounding box coordinates
  - 5th value: confidence score
  - Remaining: class probabilities

### Accuracy Impact
- **Quantization loss**: ~1-5% accuracy reduction
- **Model size reduction**: 60-80% smaller
- **Speed improvement**: 1.5-3× faster inference

---

## 🛠️ Troubleshooting

### Issue: "Module not found: tensorflow"
```bash
pip install tensorflow
```

### Issue: "ONNX conversion failed"
```bash
pip install --upgrade onnx onnx-simplifier
python convert_to_tflite.py
```

### Issue: "TFLite model is too large"
Enable aggressive quantization:
- Edit `convert_to_tflite.py`
- Change `half=True` for float16 mode
- Add `int8_dynamic=True` for integer quantization

### Issue: "Flutter: Segmentation fault when loading model"
- Verify model size matches device RAM
- Check tflite_flutter version compatibility
- Test with Python first: `python test_tflite.py`

---

## 📖 Documentation

- **YOLOv8 Export**: https://docs.ultralytics.com/modes/export/
- **TFLite Flutter**: https://github.com/tensorflow/flutter-tflite
- **Model Optimization**: https://www.tensorflow.org/lite/guide/hosted_models

---

## ⏱️ Expected Times

| Operation | Time |
|-----------|------|
| Install dependencies | 5-15 min |
| Model conversion | 2-5 min |
| Model testing | 1-2 min |
| Flutter integration | 10-20 min |
| Build & deploy | 5-10 min |
| **Total** | **23-62 min** |

---

## 🔗 Next Steps

After successful conversion:

1. ✅ Run `convert_to_tflite.py` to generate `.tflite`
2. ✅ Run `test_tflite.py` to validate
3. ✅ Run `flutter_integration_generator.py` for Flutter code
4. ✅ Copy model to Flutter `assets/`
5. ✅ Update `pubspec.yaml` with dependencies
6. ✅ Integrate detection service into your app
7. ✅ Test on physical device or emulator
8. ✅ Optimize thresholds based on accuracy needs

---

## 📞 Support

For issues or questions:
- Check YOLOv8 documentation: https://docs.ultralytics.com
- TFLite issues: https://github.com/tensorflow/tensorflow/issues
- Flutter tflite: https://pub.dev/packages/tflite_flutter

---

**Created:** 2026-03-25
**Status:** Ready for implementation
