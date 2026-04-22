# AI Navigation App

A cross-platform mobile and desktop application that uses AI-powered object detection to provide real-time environmental awareness and voice-guided navigation. Built with Flutter and Python backend with YOLOv8 object detection.

## 🎯 Features

- **Real-time Object Detection** - Detects 20+ classes including doors, humans, furniture, and architectural features
- **Voice Navigation** - Audio feedback for detected objects and navigation instructions
- **Sensor Integration** - Compass, accelerometer, and gyroscope support for orientation
- **Multi-Platform** - Runs on Android, iOS, and Windows
- **GPU Acceleration** - CUDA-enabled Python backend for fast inference
- **TFLite Support** - Converted models for on-device or backend inference
- **Cross-Device** - Backend server connects to multiple mobile clients

## 📁 Project Structure

```
project data/
├── Navigation App/           # Flutter mobile/desktop app
│   ├── lib/                 # Dart source code
│   ├── assets/              # App resources
│   │   └── models/          # TFLite models (best.tflite, yolov8n.tflite)
│   ├── android/             # Android native code
│   ├── ios/                 # iOS native code
│   ├── windows/             # Windows native code
│   ├── unified_server.py    # Flask backend server
│   └── pubspec.yaml         # Flutter dependencies
├── best_model/              # Trained PyTorch model
│   └── best.pt              # Custom trained weights (20 classes)
├── dataset/                 # Training dataset
│   ├── train/               # Training images
│   ├── valid/               # Validation images
│   └── test/                # Test images
├── tflite_conversion/       # Model conversion tools
│   ├── models/              # Converted models (ONNX, TFLite)
│   ├── flutter_integration/ # Dart integration code
│   └── conversion scripts   # Python conversion utilities
├── requirements.txt         # Python dependencies
└── yolov8n.pt              # YOLOv8 nano pretrained weights
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Flutter App (Android/iOS/Windows)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • Camera Feed                                    │  │
│  │ • Voice Navigation Service                       │  │
│  │ • Sensor Navigation (Compass, Accelerometer)     │  │
│  │ • Text-to-Speech                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ⬇️ HTTP POST
                    /detect endpoint
                          ⬇️
┌─────────────────────────────────────────────────────────┐
│     Python Flask Backend (unified_server.py)            │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • Model Loading (Custom/YOLOv8)                  │  │
│  │ • Real-time Inference (CUDA GPU)                 │  │
│  │ • Model Switching (/switch-model endpoint)       │  │
│  │ • Health Check (/health endpoint)                │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Installation & Setup

### Prerequisites

- **Python 3.8+**
- **Flutter SDK** (for mobile/desktop builds)
- **Git**
- **.NET SDK** (Windows: for NuGet packages)

### Backend Setup

1. **Activate Python environment:**
   ```bash
   cd "project data"
   .venv\Scripts\Activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server:**
   ```bash
   cd "Navigation App"
   python unified_server.py
   ```

   The backend will start on `http://0.0.0.0:5000`

### Flutter App Setup

1. **Navigate to app directory:**
   ```bash
   cd "Navigation App"
   ```

2. **Get Flutter dependencies:**
   ```bash
   flutter pub get
   ```

3. **Run on Android device:**
   ```bash
   flutter run
   ```

4. **Run on Windows:**
   ```bash
   flutter run -d windows
   ```

5. **Update backend IP in app:**
   Edit the backend URL configuration in the Flutter app to match your PC's IP address (or localhost for testing)

## 📋 Model Information

### Trained Custom Model
- **Model File:** `best_model/best.pt`
- **TFLite Version:** `Navigation App/assets/models/best.tflite`
- **Classes:** 20 object types
  - 0: Digital Board
  - 1: Door
  - 2: Glass Door
  - 3: Machine
  - 4: Table
  - 5: Chair
  - 6: Chairs
  - 7: Flower Vase
  - 8: Human
  - 9: Humans
  - 10: Round Chair
  - 11: Sofa
  - 12: Stand
  - 13: Wall
  - 14: Wall Corner
  - 15: Wall Edge
  - 16: Water Filter
  - 17: Window
  - 18: Wooden Entrance
  - 19: Wooden Stand

### Alternative YOLOv8 Model
- **Model File:** `yolov8n.pt` (backbone)
- **TFLite Version:** `Navigation App/assets/models/yolov8n.tflite`
- **Classes:** COCO dataset (80 classes)

## 🚀 API Endpoints

### Backend Server (Port 5000)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check backend status |
| `/detect` | POST | Run object detection on image |
| `/switch-model` | POST | Switch between models |

### Example: Detection Request
```bash
curl -X POST http://10.26.68.112:5000/detect \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image_data"}'
```

### Example: Model Switch
```bash
curl -X POST http://10.26.68.112:5000/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "custom"}'
```

## 📱 Mobile App Navigation

### Key Features:
- **Real-time Camera Feed** - Live detection and bounding boxes
- **Voice Guidance** - Audio alerts for detected objects and navigation instructions
- **Sensor Navigation** - Compass heading and motion tracking
- **Model Selection** - Switch between custom and YOLOv8 models

### Screen Components:
- **Main Navigation Screen** - Real-time detection visualization
- **Settings** - Backend configuration, model selection
- **Navigation History** - Previous detections and voice commands

## 🔌 Network Configuration

### Local Network Setup:
1. PC and mobile device **must be on the same WiFi network**
2. Find your PC's IP address:
   ```bash
   ipconfig  # Windows
   ```
3. Update the app configuration to use your PC's IP (e.g., `10.26.68.112:5000`)
4. Ensure the backend is running before opening the app

## 📊 Performance

- **Detection Speed:** ~80-120ms per frame (GPU)
- **Model Size:** Custom model ~100MB
- **Inference Device:** CUDA GPU (fallback to CPU)
- **Supported Batch Size:** Single frame per request

## 🛠️ Tools & Technologies

### Backend:
- **Framework:** Flask
- **Detection:** YOLOv8 (Ultralytics)
- **GPU:** PyTorch with CUDA
- **Languages:** Python 3.8+

### Mobile/Desktop:
- **Framework:** Flutter
- **Language:** Dart
- **Plugins:**
  - `camera` - Real-time camera access
  - `tflite_flutter` - On-device model inference
  - `sensors_plus` - Accelerometer, gyroscope, magnetometer
  - `flutter_tts` - Text-to-speech
  - `permission_handler` - Android/iOS permissions

## 📦 Model Conversion

To convert PyTorch models to TFLite:

```bash
cd tflite_conversion
python convert_to_tflite.py --model-path ../best_model/best.pt
```

Converted models are saved to `models/` directory.

## 🐛 Troubleshooting

### Backend Connection Issues:
- Ensure backend is running: `python unified_server.py`
- Check the PC/mobile are on same WiFi
- Verify IP address in app configuration
- Check firewall allows port 5000

### No Detections:
- Test model with sample images
- Ensure adequate lighting for object detection
- Point camera at defined object classes
- Check model confidence threshold settings

### Flutter Build Errors:
- On Windows, ensure NuGet is installed: `nuget.exe` in PATH
- Run: `flutter clean` and `flutter pub get`
- Update dependencies: `flutter pub upgrade`

## 📞 Support

For issues or questions:
1. Check the project logs in `Navigation App/logs/`
2. Verify backend logs in the terminal
3. Ensure all dependencies are installed with correct versions

## 📝 License

This project is part of an AI Navigation system for accessibility and awareness.

---

**Status:** ✅ Fully Functional (Backend + Flutter App)
- Backend: Python Flask server with YOLOv8 detection
- Frontend: Flutter app with real-time camera, voice, and sensor integration
- Models: Trained custom model (20 classes) + YOLOv8 variant
#   O b j e c t _ D e t e c t i o n _ a n d _ N a v i g a t i o n 2  
 