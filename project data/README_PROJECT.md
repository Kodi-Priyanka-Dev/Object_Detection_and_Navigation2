# 🎯 AI-Powered Indoor Navigation & Object Detection System

A complete real-time object detection and indoor navigation solution combining **YOLOv8 NANO** deep learning with **Flutter mobile app** and **Flask backend** for accessibility and autonomous systems.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Objects Detected](#objects-detected)
- [API Documentation](#api-documentation)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project provides an **end-to-end solution for real-time object detection** in indoor environments. It's designed to:

✅ Assist visually impaired users with real-time obstacle detection  
✅ Guide autonomous robots and drones through indoor spaces  
✅ Enable security monitoring and crowd detection  
✅ Provide accessible navigation with voice guidance  
✅ Work offline with on-device inference (TFLite)  
✅ Achieve 30+ FPS real-time detection on mobile devices  

### Use Cases:
- 🏢 **Indoor Navigation** — Navigate buildings, offices, hospitals, museums
- ♿ **Accessibility** — Obstacle detection for visually impaired users
- 🚁 **Autonomous Systems** — Provide perception for robots and drones
- 📹 **Security & Monitoring** — Detect people, objects, and anomalies
- 🏭 **Industrial** — Monitor environments and detect hazards

---

## ✨ Key Features

### Real-time Detection
- **18 object classes** with confidence scoring
- **30+ FPS** detection on mobile
- Bounding box coordinates and dimensions

### Distance Estimation
- Calculates real-world distance to detected objects
- Uses camera calibration and object width estimation

### Navigation Assistance
- Obstacle detection and path calculation
- Directional guidance (Left, Right, Forward)
- Optimal movement recommendations

### Voice & Visual Alerts
- Text-to-speech announcements
- Pop-up notifications for critical objects
- Real-time bounding box visualization

### Performance Optimized
- Lightweight YOLOv8N model (3.05 MB TFLite)
- Frame skipping for reduced latency
- GPU acceleration support (CUDA backend)

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Python + Flask | 3.8+ |
| **AI Model** | YOLOv8 NANO | Latest |
| **ML Framework** | PyTorch | Latest |
| **Mobile App** | Flutter | 3.0+ |
| **Mobile Inference** | TensorFlow Lite | Latest |
| **Image Processing** | OpenCV | Latest |
| **GPU Acceleration** | CUDA | Optional |
| **Dataset Management** | Roboflow | YOLO Format |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Flutter 3.0+ (for mobile app)
- CUDA 11.0+ (optional, for GPU acceleration)
- 4GB RAM minimum

### 1. Backend Setup (5 minutes)

```bash
# Navigate to project directory
cd "project data"

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
cd "Navigation App"
python unified_server.py
```

Backend runs at: `http://localhost:5000`

### 2. Mobile App Setup (10 minutes)

```bash
# Install Flutter dependencies
cd "Navigation App"
flutter pub get

# Run on device/emulator
flutter run

# Or build for release
flutter build apk      # Android
flutter build ios      # iOS
```

### 3. Test Detection

```bash
# In a new terminal, test the backend
curl -X POST http://localhost:5000/detect \
  -F "image=@test_image.jpg"
```

---

## 📁 Project Structure

```
project data/
├── Navigation App/                 # Flutter mobile application
│   ├── lib/                        # Flutter source code
│   ├── android/                    # Android configuration
│   ├── ios/                        # iOS configuration
│   ├── unified_server.py           # Backend Flask server ⭐
│   ├── backend_service.py          # Service layer
│   ├── pubspec.yaml                # Flutter dependencies
│   └── logs/                       # Backend logs
│
├── dataset/                        # Training dataset (YOLO format)
│   ├── train/                      # Training images & labels
│   ├── valid/                      # Validation data
│   ├── test/                       # Test data
│   └── data.yaml                   # Dataset configuration
│
├── best_model/                     # Trained YOLOv8 models
│   ├── best.pt                     # Main PyTorch model
│   └── best_saved_model/           # Exported format
│
├── tflite_conversion/              # TFLite model conversion
│   ├── convert_yolov8n_to_tflite.py
│   ├── yolov8n.tflite              # Mobile model
│   └── flutter_integration_generator.py
│
├── train.py, train2.py, train3.py  # Model training scripts
├── test_detection.py               # Detection testing
├── validate_model.py               # Model validation
├── consolidate_classes.py           # Class consolidation
├── prepare_new_dataset.py          # Dataset preparation
├── requirements.txt                # Python dependencies
└── README_PROJECT.md               # This file
```

---

## 📥 Installation

### Full Setup Guide

#### Step 1: Clone/Setup Project
```bash
cd "AI project/project data"
```

#### Step 2: Install Python Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### Step 3: Verify Dataset
```bash
# Check if dataset exists
ls dataset/
# Should show: train/, valid/, test/, data.yaml
```

#### Step 4: Download Pre-trained Model
```bash
# Model is included as best.pt
# For TFLite conversion:
python tflite_conversion/convert_yolov8n_to_tflite.py
```

#### Step 5: Setup Backend Logging
```bash
# Backend logs are auto-created at:
# Navigation App/logs/backend_YYYYMMDD_HHMMSS.log
```

#### Step 6: Configure Flutter (Mobile)
```bash
cd "Navigation App"
flutter pub get
flutter pub upgrade
```

---

## 💻 Usage

### Backend API

#### Detect Objects in Image
```bash
POST /detect
Content-Type: multipart/form-data

Parameters:
  - image: Image file (JPG/PNG)
  - confidence: (optional) Confidence threshold 0-1

Response:
{
  "success": true,
  "detections": [
    {
      "class": "human",
      "confidence": 0.95,
      "x": 320,
      "y": 240,
      "width": 100,
      "height": 150,
      "distance_m": 2.5
    }
  ],
  "navigation": {
    "direction": "left",
    "closest_object": "human",
    "distance_m": 2.5
  }
}
```

#### Get Health Status
```bash
GET /health
Response: {"status": "ok", "model": "yolov8n"}
```

### Flutter Mobile App

1. **Launch App** — Starts camera feed
2. **Point at Objects** — Real-time detection overlay
3. **Receive Alerts** — Pop-ups for critical objects
4. **Voice Guidance** — Speaker announces objects/directions
5. **Settings** — Adjust confidence thresholds per class

### Command Line Testing

```bash
# Test detection
python test_detection.py

# Validate model performance
python validate_model.py

# Train custom model
python train3.py

# Consolidate duplicate classes
python consolidate_complete.py
```

---

## 🎯 Objects Detected (18 Classes)

| # | Class | Confidence Threshold | Use Case |
|---|-------|-------------------|----------|
| 0 | Digital Board | 30% | Landmark detection |
| 1 | Door | 25% | Navigation, passage detection |
| 2 | Glass Door | 25% | Same as door |
| 3 | Machine | 30% | Equipment detection |
| 4 | Table | 30% | Obstacle avoidance |
| 5 | chair | 30% | Seating detection |
| 6 | flowervase | 30% | Decorative objects |
| 7 | round chair | 30% | Seating detection |
| 8 | human | 48% | Person avoidance ⭐ |
| 9 | sofa | 30% | Furniture detection |
| 10 | stand | 30% | Obstacle detection |
| 11 | wall | 30% | Environment mapping |
| 12 | wall corner | 30% | Navigation landmarks |
| 13 | wall edge | 30% | Navigation landmarks |
| 14 | water filter | 30% | Equipment detection |
| 15 | window | 35% | Room boundaries |
| 16 | wooden entrance | 25% | Passage detection |
| 17 | wooden stand | 30% | Obstacle detection |

---

## 📊 Performance

### Model Specifications
- **Architecture**: YOLOv8 NANO
- **Input Size**: 640×480 pixels
- **Inference Speed**: 30-60 FPS (mobile)
- **Model Size**: 3.05 MB (TFLite)
- **Accuracy**: mAP50 ≈ 0.85+

### Device Requirements
- **Mobile**: 4GB RAM, Android 8.0+, iOS 11.0+
- **Backend**: 2GB RAM, Python 3.8+
- **GPU**: NVIDIA CUDA for acceleration (optional)

### Optimization Techniques
- Frame skipping (process every N frames)
- JPEG compression (80% quality)
- Model quantization (TF32 on backend)
- Batch processing support

---

## 🔧 Configuration

### Backend Configuration (unified_server.py)

```python
# Model selection
MODEL_NAME = "yolov8n"  # or "yolov8s", "yolov8m", "yolov8l"

# Confidence thresholds
CONFIDENCE_THRESHOLD = 0.25  # Default: 25%

# Classes requiring higher confidence
HIGH_CONFIDENCE_CLASSES = {
    "human": 0.48,          # 48% for people
    "chair": 0.30,
    "door": 0.25
}

# Device selection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

### Model Training (train3.py)

```python
# Training parameters
EPOCHS = 50
BATCH_SIZE = 16
IMG_SIZE = 640
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
activate virtual environment first:
.venv\Scripts\activate

Then install dependencies:
pip install -r requirements.txt
```

### CUDA Not Found

**Error**: `CUDA out of memory`

**Solution**:
```python
# In unified_server.py, force CPU:
DEVICE = "cpu"
```

### Detection Accuracy Low

**Solution**:
```bash
# 1. Check confidence thresholds
# 2. Retrain on custom dataset
python train3.py --data dataset/data.yaml --epochs 100

# 3. Validate performance
python validate_model.py
```

### Mobile App Can't Connect to Backend

**Solution**:
```
1. Ensure backend is running: python unified_server.py
2. Check backend is accessible at localhost:5000
3. On emulator: use http://10.0.2.2:5000
4. On device: use IP address of backend machine
5. Check firewall rules allow port 5000
```

### Class Categories Missing

**Solution**:
```bash
# Consolidate duplicate classes
python consolidate_complete.py

# Update data.yaml
# Retrain model
python train3.py
```

---

## 📈 Future Improvements

- [ ] Real-time video streaming support
- [ ] Multi-object tracking (MOT)
- [ ] Depth estimation from single image
- [ ] Custom model training UI
- [ ] Cloud deployment (AWS, Google Cloud)
- [ ] Advanced navigation algorithms (A*, Dijkstra)
- [ ] 3D environment mapping
- [ ] Voice command integration
- [ ] Offline update mechanism
- [ ] Privacy-preserving on-device processing

---

## 📝 Dataset Preparation

### Preparing New Datasets

```bash
# Convert Roboflow XML annotations to YOLO format
python prepare_new_dataset.py

# Consolidate duplicate classes
python consolidate_complete.py

# Retrain with new data
python train3.py --data dataset/data.yaml
```

### Class Consolidation

The project uses **18 consolidated classes** (originally 20):
- Merged "chairs" → "chair"
- Merged "humans" → "human"

To re-consolidate:
```bash
python consolidate_complete.py
```

---

## 📚 Documentation Files

- **PROJECT_DOCUMENTATION.md** — Comprehensive documentation
- **PROJECT_STATUS.md** — Current project status
- **QUICK_START.md** — Quick reference guide
- **YOLOV8N_IMPLEMENTATION_GUIDE.md** — Model-specific guide
- **BACKEND_README.md** — Backend API documentation
- **FEATURES.md** — Detailed feature list

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Model accuracy optimization
- Performance benchmarking
- New object classes
- Platform support (web, desktop)
- Documentation updates

---

## 📄 License

This project is developed for research and accessibility purposes.

---

## 👤 Author & Support

For issues, questions, or contributions:
1. Check documentation files in `project data/`
2. Review troubleshooting section above
3. Check backend logs: `Navigation App/logs/`

---

## 🎓 Learning Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com
- **Flutter Docs**: https://flutter.dev/docs
- **Flask Guide**: https://flask.palletsprojects.com
- **PyTorch Tutorial**: https://pytorch.org/tutorials

---

## 📊 Project Status

| Component | Status | Version |
|-----------|--------|---------|
| Backend API | ✅ Production | 2.0 |
| Mobile App | ✅ Production | 1.5 |
| YOLOv8N Model | ✅ Trained | Latest |
| TFLite Conversion | ✅ Complete | 1.0 |
| Documentation | ✅ Complete | 2.0 |
| Class Consolidation | ✅ Complete | 18 classes |

---

**Last Updated**: April 7, 2026  
**Version**: 2.0
