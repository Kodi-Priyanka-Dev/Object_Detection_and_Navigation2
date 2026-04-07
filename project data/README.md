# AI Navigation Assistant (YOLOv8 + Flask + Flutter)

End-to-end indoor navigation assistance system combining:
- **Computer vision** (YOLOv8) for real-time object/door detection
- **Backend API** (Flask) for frame inference + navigation decisions
- **Mobile app** (Flutter) for camera capture, sensor fusion (compass/IMU), and voice guidance

If you’re new to this repo, start with:
- `QUICK_START.txt` (fastest way to run tests)
- `PROJECT_README.md` (full architecture + deep dive)

---

## Repository layout

High-level structure:

- `Navigation App/` — Flutter app + Python backend server used by the app
  - `Navigation App/backend_service.py` — Flask backend (port **5000**)
  - `Navigation App/lib/` — Flutter source
  - `Navigation App/README.md` — app + backend documentation
  - `Navigation App/QUICKSTART.md` — mobile quickstart
- `best_model/best.pt` — trained YOLO weights used by detection code
- `door_detection_visualization.py` — local webcam visualization (no backend needed)
- `test_backend_detection.py` — backend API test client
- `dataset/` — training data (train/valid/test) + `data.yaml`
- `runs/` — training/detection outputs

More docs:
- `DOCUMENTATION_INDEX.txt` — map of all documentation
- `INTEGRATION_GUIDE.txt` — integration workflow + thresholds
- `DOOR_DETECTION_README.txt` — visualization details

---

## Prerequisites

### Python
- Python installed (project docs mention 3.12; other versions may work)
- A Python environment (this repo commonly uses `.venv`)

### Flutter (for mobile app)
- Flutter SDK installed
- Android device or emulator

---

## Quick start (Windows / PowerShell)

This repo supports three common ways to test the system. These steps are mirrored in `QUICK_START.txt`.

> Tip: if your repo folder contains spaces, wrap paths in quotes.

If you use a virtual environment, create it once from the repo root:

```powershell
python -m venv .venv
```

Then install Python packages (choose what you need):

```powershell
# For root scripts (training/inference/visualization)
pip install -r requirements.txt

# For the Flask backend used by the Flutter app
pip install -r "Navigation App/backend_requirements.txt"
```

### Method 1 — Local detection (fastest, no backend)

Runs YOLO on your webcam and overlays detections/arrows.

```powershell
cd "<repo-root>"
.\.venv\Scripts\Activate.ps1
python door_detection_visualization.py
```

Press **q** to quit.

### Method 2 — Backend service test (Flask API)

1) Start the backend:

```powershell
cd "<repo-root>\Navigation App"
.\.venv\Scripts\Activate.ps1
python backend_service.py
```

2) In a new terminal, run the client test:

```powershell
cd "<repo-root>"
.\.venv\Scripts\Activate.ps1
python test_backend_detection.py
```

### Method 3 — Full system (Flutter app + backend)

1) Start the backend (same as Method 2).

2) Run the Flutter app:

```powershell
cd "<repo-root>\Navigation App"
flutter clean
flutter pub get
flutter run
```

3) Ensure the phone and the backend machine are on the **same Wi‑Fi network**.

If the app needs a backend IP configured, see `Navigation App/README.md` for where to set `baseUrl`.

---

## Dependencies

This repository has two Python dependency lists (depending on what you run):

- `requirements.txt` — Python environment for training/inference scripts in the repo root
- `Navigation App/backend_requirements.txt` — backend server dependencies

Install whichever applies to your workflow.

---

## Model & data notes

- The backend and visualization scripts expect a YOLO model at: `best_model/best.pt`
- Training data is under: `dataset/` (with configuration in `dataset/data.yaml`)

---

## Troubleshooting

Common checks:

- **Backend not reachable**: verify the backend is running and listening on port **5000**.
- **Model not found**: verify `best_model/best.pt` exists.
- **Slow FPS**: close GPU-heavy apps, test Method 1 first.

More detailed troubleshooting:
- `PROJECT_README.md`
- `INTEGRATION_GUIDE.txt`
- `Navigation App/BACKEND_README.md`

---

## Documentation map

- Project overview: `PROJECT_README.md`
- Fast start & test methods: `QUICK_START.txt`
- Integration workflow: `INTEGRATION_GUIDE.txt`
- Flutter app guide: `Navigation App/README.md`
- Backend deep dive: `Navigation App/BACKEND_README.md`
