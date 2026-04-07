# 🤖 AI Navigation Assistant - Complete Project Guide

A Flutter mobile app powered by YOLOv8 object detection that provides real-time navigation assistance, obstacle detection, and voice guidance for indoor navigation.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Backend Setup (Python)](#backend-setup-python)
5. [Frontend Setup (Flutter)](#frontend-setup-flutter)
6. [Running the Application](#running-the-application)
7. [Features](#features)
8. [API Documentation](#api-documentation)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

The **AI Navigation Assistant** is an intelligent navigation app that uses computer vision to detect obstacles, doors, and people in real-time. It provides:

- **Real-time object detection** using YOLOv8 neural networks
- **Distance estimation** for detected objects
- **Voice guidance** for turn-by-turn navigation
- **Visual indicators** showing navigation direction (left/right/forward)
- **Pop-up alerts** for critical obstacles (doors, people)
- **Live camera feed** with annotated detections

### Use Cases:
- 🏢 **Indoor Navigation** - Navigate through buildings, offices, hospitals
- ♿ **Accessibility** - Assist visually impaired users with obstacle avoidance
- 🤖 **Autonomous Robots** - Guide robotic systems through environments
- 🚗 **Smart Navigation** - Real-time collision avoidance

---

## 🛠️ Technology Stack

### Backend (Python)
| Component | Version | Purpose |
|-----------|---------|---------|
| Flask | Latest | REST API server |
| YOLO | YOLOv8 | Object detection model |
| OpenCV | Latest | Image processing |
| PyTorch | Latest | Deep learning framework |
| NumPy | Latest | Numerical computations |

### Frontend (Flutter)
| Component | Version | Purpose |
|-----------|---------|---------|
| Flutter | 3.11.1+ | Mobile app framework |
| Camera | 0.11.0+ | Access device camera |
| HTTP | 1.1.0+ | Backend communication |
| Flutter TTS | 4.2.0+ | Text-to-speech |
| Permission Handler | 11.4.0+ | Runtime permissions |

---

## 📁 Project Structure

```
Navigation App/
├── lib/                              # Flutter app source code
│   ├── main.dart                    # App entry point
│   ├── models/
│   │   └── detection_model.dart    # Data models for detections
│   ├── screens/
│   │   └── home_screen.dart        # Main camera/detection screen
│   ├── services/
│   │   ├── detection_service.dart  # Backend communication service
│   │   └── voice_service.dart      # Text-to-speech service
│   └── widgets/
│       ├── detection_overlay.dart  # Displays object labels & positions
│       ├── navigation_arrows.dart  # Left/Right/Forward indicators
│       ├── navigation_popup.dart   # Alert dialogs
│       └── navigation_path.dart    # Tesla-style navigation line
│
├── android/                          # Android configuration
│   └── app/build.gradle.kts         # Android app settings
│
├── ios/                              # iOS configuration
│   └── Runner/                       # iOS app setup
│
├── backend_service.py                # Flask backend server
├── backend_requirements.txt           # Python dependencies
├── pubspec.yaml                      # Flutter dependencies
│
├── QUICKSTART.md                     # Quick start guide
├── FEATURES.md                       # Detailed features
├── SUMMARY.md                        # Project summary
└── README.md                         # This file
```

---

## 🐍 Backend Setup (Python)

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- 2GB minimum RAM
- GPU recommended (NVIDIA CUDA for faster inference)

### Step 1: Install Dependencies

Open **PowerShell** in the `Navigation App` folder:

```powershell
# Using requirements file (recommended)
pip install -r backend_requirements.txt

# OR manually install
pip install flask flask-cors ultralytics opencv-python numpy
```

### Step 2: Download YOLO Model

The model file should be located at: `../best_model/best.pt`

If not present:
```powershell
# The model will auto-download on first run, or place it manually
# Place your trained YOLO model at: ../best_model/best.pt
```

### Step 3: Start Backend Server

```powershell
python backend_service.py
```

**Expected Output:**
```
============================================================
BACKEND SERVICE STARTUP
============================================================
[1/4] PyTorch CUDA disabled (CPU mode)
[2/4] Flask imported successfully
[3/4] Loading PyTorch and YOLO... (this may take 10-30 seconds)
[4/4] Loading model from: ../best_model/best.pt
      ✅ Model loaded successfully!
============================================================
✅ BACKEND READY - Model loaded and listening on port 5000
============================================================
```

**⚠️ IMPORTANT:** Keep this terminal open while using the app!

---

## 📱 Frontend Setup (Flutter)

### Prerequisites
- Flutter 3.11.1 or higher
- Android SDK (for Android devices)
- Xcode (for iOS devices)
- A connected physical device or emulator

### Step 1: Install Flutter Dependencies

Open **PowerShell** in the `Navigation App` folder:

```powershell
flutter pub get
```

### Step 2: Configure Backend IP Address

Edit `lib/services/detection_service.dart`:

```dart
// Change this to your computer's IP address
static const String baseUrl = 'http://YOUR_IP:5000';
```

**To find your IP address:**
```powershell
ipconfig
```

Look for "IPv4 Address" (e.g., `192.168.1.100`)

### Step 3: Request Permissions

The app requires camera permission. This is requested automatically on first launch.

---

## 🚀 Running the Application

### Option 1: Physical Android Device

**Terminal 1 - Start Backend:**
```powershell
cd "Navigation App"
python backend_service.py
```

**Terminal 2 - Connect Device & Run App:**
```powershell
adb connect DEVICE_IP:5555  # e.g., 10.26.74.132:5555
cd "Navigation App"
flutter run
```

### Option 2: Android Emulator

**Terminal 1 - Start Backend:**
```powershell
python backend_service.py
```

**Terminal 2 - Run on Emulator:**
```powershell
cd "Navigation App"
flutter run
```

### Option 3: iOS Device

**Terminal 1 - Start Backend:**
```powershell
python backend_service.py
```

**Terminal 2 - Run on iOS:**
```powershell
cd "Navigation App"
flutter run
```

---

## ✨ Features

### 🎥 Real-Time Detection
- Continuous frame capture from device camera
- Processes frames at ~1-5 FPS (depending on device)
- Shows live detection results with minimal latency

### 🏷️ Object Labels
- **Format:** `[Object Name] - [Distance] m`
- **Color-coded:** Different colors for different object types
- **Position:** Labels appear at detected object centers

### 📍 Distance Estimation
- Calculates real-world distance based on object pixel width
- Uses focal length calibration for accuracy
- Displays distance in meters (m)

### 🗣️ Voice Guidance
Automatic text-to-speech announcements:
- Door detected: *"Door detected at 1.5 meters. Do you want to open and go?"*
- Human detected: *"Human detected on your right. Deviate left."*
- Navigation instructions with 2-second cooldown to avoid repetition

### 🧭 Navigation Indicators
| Indicator | Meaning | Trigger |
|-----------|---------|---------|
| ← LEFT | Move left | Human on right side |
| → RIGHT | Move right | Human on left side |
| ↑ FORWARD | Go forward | Door ahead |
| ⚠️ STOP | Stop immediately | Human directly in path |

### 🔔 Smart Pop-ups

**Door Alert:**
- Appears when door is detected < 2 meters away
- Options: "Open and Go" (Yes/No)
- Closes when "No" is clicked
- Triggers voice announcement

**Human Alert:**
- Triggers when person detected < 2 meters
- Shows direction (left/right)
- Recommends avoidance direction
- Color-coded red for urgency

### 🛣️ Navigation Path (Tesla-style)
- Shows virtual navigation line
- Indicates recommended direction
- Updates based on obstacle positions
- Provides visual guidance overlay

---

## 📡 API Documentation

### Backend Endpoints

#### 1. Health Check
```
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### 2. Object Detection
```
POST /detect
Content-Type: application/json
```

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response:**
```json
{
  "detections": [
    {
      "class": "door",
      "confidence": 0.95,
      "x": 320,
      "y": 240,
      "width": 150,
      "height": 300,
      "distance": 1.5
    },
    {
      "class": "person",
      "confidence": 0.87,
      "x": 640,
      "y": 360,
      "width": 100,
      "height": 250,
      "distance": 2.3
    }
  ],
  "processing_time_ms": 145
}
```

### Communication Flow

```
Flutter App (Mobile)
    ↓
1. Capture frame from camera
2. Convert to JPEG
3. Encode to Base64
    ↓
POST /detect
    ↓
Python Backend (Flask)
1. Decode Base64 image
2. Run YOLO detection
3. Calculate distances
    ↓
Return JSON response
    ↓
Flutter App
1. Parse detections
2. Update UI overlay
3. Trigger alerts/voice
```

---

## 🔧 Configuration

### Backend Configuration

**File:** `backend_service.py`

```python
# Distance Estimation Parameters
KNOWN_WIDTH = 0.9        # meters (door width)
FOCAL_LENGTH = 800       # camera calibration value

# Server Settings
HOST = '0.0.0.0'         # Listen on all interfaces
PORT = 5000              # Flask server port
```

### Frontend Configuration

**File:** `lib/services/detection_service.dart`

```dart
// Backend URL (change to your IP)
static const String baseUrl = 'http://10.26.67.141:5000';

// Timeouts
const Duration requestTimeout = Duration(seconds: 15);
const Duration healthCheckTimeout = Duration(seconds: 5);
```

**File:** `lib/screens/home_screen.dart`

```dart
// Detection sensitivity
static const double DOOR_DISTANCE_THRESHOLD = 2.0;  // meters
static const double HUMAN_DISTANCE_THRESHOLD = 2.0; // meters

// Voice settings
static const Duration VOICE_COOLDOWN = Duration(seconds: 2);
```

---

## 🐛 Troubleshooting

### Backend Issues

#### ❌ "Model not loaded"
```
Solution:
1. Check model file exists: ../best_model/best.pt
2. Ensure sufficient disk space
3. Run: pip install ultralytics --upgrade
4. Reinstall PyTorch: pip install torch torchvision
```

#### ❌ "CUDA out of memory"
```
Solution:
Backend runs on CPU by default (CUDA disabled)
If you need GPU:
1. In backend_service.py, comment line: os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
2. Ensure NVIDIA CUDA toolkit is installed
```

#### ❌ "Address already in use"
```
Solution:
Port 5000 is already in use
1. Kill existing process: netstat -ano | findstr :5000
2. Change port in backend_service.py if needed
3. Use different port and update Flutter app config
```

### Frontend Issues

#### ❌ "Connection refused"
```
Solution:
1. Check backend is running: python backend_service.py
2. Verify IP address in detection_service.dart
3. Ensure device and backend on same WiFi
4. Try: ping YOUR_IP (should succeed)
5. Check firewall allows port 5000
```

#### ❌ "Camera permission denied"
```
Solution:
1. Grant camera permission when prompted
2. Manual grant: Settings → App Permissions → Camera → Allow
3. Reinstall app to trigger permission dialog
```

#### ❌ "Slow detection / High latency"
```
Solution:
1. Reduce frame resolution in home_screen.dart
2. Decrease frame rate (skip frames)
3. Use lower quality JPEG compression
4. Split app and backend on separate networks
5. Upgrade device hardware or use GPU backend
```

#### ❌ "Labels appear in wrong positions"
```
Solution:
1. Calibrate KNOWN_WIDTH and FOCAL_LENGTH in backend
2. Check camera resolution matches display
3. Verify coordinate transformation in detection_overlay.dart
```

---

## 📊 Performance Metrics

### Expected Performance

| Metric | Value | Hardware |
|--------|-------|----------|
| Detection Speed | 1-5 FPS | Snapdragon 888+ |
| Average Latency | 200-500ms | Per frame |
| Memory Usage | 500-800MB | Peak |
| Battery Drain | 15-20%/hour | Continuous detection |

### Optimization Tips

1. **Reduce Frame Resolution:**
   - Lower quality = faster processing
   - Edit: `homeScreen.dart` camera settings

2. **Skip Frames:**
   - Process every 2nd or 3rd frame
   - Reduces latency perception

3. **Compress JPEG:**
   - Lower quality before transmission
   - Saves bandwidth

4. **Use GPU Backend:**
   - 3-5x faster than CPU
   - Requires NVIDIA CUDA

---

## 📚 Additional Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenCV Documentation](https://docs.opencv.org/)

---

## 📝 File Descriptions

| File | Purpose |
|------|---------|
| `main.dart` | App initialization |
| `lib/screens/home_screen.dart` | Main UI with camera |
| `lib/services/detection_service.dart` | Backend API communication |
| `lib/models/detection_model.dart` | Data structures |
| `lib/widgets/detection_overlay.dart` | Draw detected objects |
| `lib/widgets/navigation_arrows.dart` | Direction indicators |
| `lib/widgets/navigation_popup.dart` | Alert dialogs |
| `lib/widgets/navigation_path.dart` | Navigation line widget |
| `backend_service.py` | Flask API server |

---

## 🔐 Security Considerations

- ⚠️ Backend runs on local network only
- 🔒 No authentication required (internal use)
- 📱 Camera frames temporarily stored in memory only
- 🚫 No data persisted to external servers

---

## 📞 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review [QUICKSTART.md](QUICKSTART.md) for setup
3. See [FEATURES.md](FEATURES.md) for feature details

---

**Last Updated:** March 2026
**Version:** 1.0.0
**Status:** Active Development
