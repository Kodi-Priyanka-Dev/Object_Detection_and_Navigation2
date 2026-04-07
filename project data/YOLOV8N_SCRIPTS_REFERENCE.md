# YOLOv8n Scripts — Quick Reference Guide

## Overview

The improved `yolov8n_scripts_improved.py` provides **5 ready-to-use detection scripts** with smart filtering for **23 target COCO classes** (down from 80):

- **1 Human class** — highest priority (red boxes)
- **5 Accessories** — gold boxes
- **11 Electronics** — orange boxes  
- **6 Furniture** — green boxes

Each script includes **auto-download capability** — if YOLOv8n model is missing, it automatically downloads from Ultralytics.

---

## Installation

```bash
# Install dependencies
pip install ultralytics opencv-python numpy

# Verify download
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

## Script 1: Image Detection

**Function**: `detect_objects_in_image(image_path, output_path='result.jpg', conf=0.5)`

**Purpose**: Annotate a single image with bounding boxes (filtered classes)

**Example**:
```python
from yolov8n_scripts_improved import detect_objects_in_image

detect_objects_in_image('photo.jpg', 'photo_annotated.jpg', conf=0.5)
```

**Output**:
```
==================================================
  HUMANS (priority): 2 detected
==================================================
  ★ person  | conf: 0.892 | box: (100, 150, 250, 500)
  ★ person  | conf: 0.834 | box: (300, 200, 450, 600)

  OTHER TARGET CLASSES: 5 detected
--------------------------------------------------
  [Furniture    ] chair          | conf: 0.756
  [Electronics  ] laptop         | conf: 0.812
  [Accessories  ] backpack       | conf: 0.701
  [Furniture    ] bed            | conf: 0.689
  [Electronics  ] tv             | conf: 0.823
```

**Parameters**:
- `image_path` — Input image file path
- `output_path` — Where to save annotated image (default: `result.jpg`)
- `conf` — Confidence threshold 0-1 (default: 0.5)

---

## Script 2: Real-time Webcam Detection

**Function**: `webcam_detection(conf=0.5, fps_limit=30)`

**Purpose**: Live detection from webcam with HUD display

**Example**:
```python
from yolov8n_scripts_improved import webcam_detection

webcam_detection(conf=0.5, fps_limit=15)  # 15 FPS for slower machines
```

**Controls**:
| Key | Action |
|-----|--------|
| `q` | Quit |
| `s` | Save screenshot |

**Features**:
- Red boxes for humans (thicker)
- Different colors per category
- Frame counter in top-left
- Human count in red
- Real-time inferencing

**Parameters**:
- `conf` — Confidence threshold (default: 0.5)
- `fps_limit` — Target FPS (default: 30, reduce for slower hardware)

---

## Script 3: Video File Processing

**Function**: `process_video(input_video, output_video='output.mp4', conf=0.5)`

**Purpose**: Process entire video and save annotated output

**Example**:
```python
from yolov8n_scripts_improved import process_video

process_video('input.mp4', 'annotated.mp4', conf=0.5)
```

**Output**:
```
Video: 1920x1080 @ 30fps — 1800 frames
Progress: 30/1800 (1.7%)
Progress: 60/1800 (3.3%)
...
Done! Output saved to: annotated.mp4
```

**Parameters**:
- `input_video` — Path to input video
- `output_video` — Where to save annotated video (default: `output.mp4`)
- `conf` — Confidence threshold (default: 0.5)

---

## Script 4: Object Analysis & Statistics

**Class**: `ObjectAnalyzer(model_path='yolov8n.pt')`

**Purpose**: Count and analyze objects with detailed statistics

**Usage**:
```python
from yolov8n_scripts_improved import ObjectAnalyzer

analyzer = ObjectAnalyzer()

# Analyze single image
analyzer.analyze_image('photo.jpg')
analyzer.print_statistics()

# Or analyze video (every 5 seconds)
analyzer.analyze_video('video.mp4', interval=5)
```

**Output Example**:
```
=======================================================
  DETECTION STATISTICS
=======================================================

  [HUMANS — PRIORITY]
  ★ person          Count:   42  Avg Conf: 0.876

  [ACCESSORIES]
    handbag             Count:    3  Avg Conf: 0.724

  [ELECTRONICS]
    laptop              Count:    8  Avg Conf: 0.812
    tv                  Count:    5  Avg Conf: 0.789

  [FURNITURE]
    chair               Count:   15  Avg Conf: 0.745
    bed                 Count:    2  Avg Conf: 0.834

  -------------------------------------------------------
  Total detections: 75
```

**Methods**:
- `analyzeimage(path, conf=0.5)` — Single image analysis
- `analyze_video(path, conf=0.5, interval=5)` — Video analysis every N seconds
- `print_statistics()` — Print collected stats
- `get_statistics()` — Return stats as dict

**Parameters**:
- `conf` — Confidence threshold (default: 0.5)
- `interval` — Analyze every N seconds of video (default: 5)

---

## Script 5: Custom Filtering

**Function**: `detect_specific_objects(image_path, target_classes=None, conf=0.5)`

**Purpose**: Detect custom class subsets (not just default 23)

**Example 1 — Default (23 classes)**:
```python
from yolov8n_scripts_improved import detect_specific_objects

detect_specific_objects('photo.jpg')  # Uses all 23 target classes
```

**Example 2 — Custom subset (only humans + chairs)**:
```python
from yolov8n_scripts_improved import detect_specific_objects

detect_specific_objects('photo.jpg', target_classes=['person', 'chair'])
```

**Example 3 — Only electronics**:
```python
from yolov8n_scripts_improved import detect_specific_objects, ELECTRONICS_CLASSES

detect_specific_objects('photo.jpg', target_classes=ELECTRONICS_CLASSES)
```

**Parameters**:
- `image_path` — Input image
- `target_classes` — List of class names (None = use all 23 defaults)
- `conf` — Confidence threshold (default: 0.5)

---

## Class Categories Explained

### HUMANS (Priority) — 1 class
- `person` — Highest priority, red boxes, thicker bounding box

### ACCESSORIES — 5 classes
- `handbag` — Bags, purses
- `tie` — Neckties
- `suitcase` — Luggage, cases
- `umbrella` — Umbrellas
- `backpack` — Backpacks

### ELECTRONICS — 11 classes
- `tv` — Television, monitor
- `laptop` — Laptop computers
- `mouse` — Computer mouse
- `remote` — Remote controls
- `keyboard` — Keyboards
- `cell phone` — Mobile phones
- `microwave` — Microwave ovens
- `oven` — Kitchen ovens
- `toaster` — Toasters
- `refrigerator` — Fridges
- `hair drier` — Hair dryers

### FURNITURE — 6 classes
- `chair` — Chairs
- `couch` — Sofas, couches
- `bed` — Beds
- `dining table` — Tables
- `toilet` — Toilets
- `sink` — Sinks

---

## Configuration

### Color Scheme (BGR format)

| Category | Color | RGB Code | Use |
|----------|-------|----------|-----|
| Human | Red | (0, 0, 255) | Highest priority |
| Accessory | Gold | (0, 215, 255) | Medium priority |
| Electronics | Orange | (255, 180, 0) | Medium priority |
| Furniture | Green | (0, 200, 100) | Lower priority |

To customize colors, modify `CATEGORY_COLORS` dict:
```python
CATEGORY_COLORS = {
    'human':       (0, 0, 255),         # Red
    'accessory':   (0, 215, 255),       # Gold
    'electronics': (255, 180, 0),       # Blue-orange
    'furniture':   (0, 200, 100),       # Green
}
```

---

## Common Usage Patterns

### Pattern 1: Batch Process Images
```python
from pathlib import Path
from yolov8n_scripts_improved import detect_objects_in_image

for img_path in Path('images/').glob('*.jpg'):
    detect_objects_in_image(str(img_path), f'output/{img_path.stem}_detect.jpg')
```

### Pattern 2: Real-time Monitoring
```python
from yolov8n_scripts_improved import webcam_detection

# Monitor with reduced FPS for slower computer
webcam_detection(conf=0.6, fps_limit=10)
```

### Pattern 3: Statistics Collection
```python
from yolov8n_scripts_improved import ObjectAnalyzer

analyzer = ObjectAnalyzer()
for video in ['video1.mp4', 'video2.mp4', 'video3.mp4']:
    analyzer.analyze_video(video, interval=10)
    
stats = analyzer.get_statistics()
print(f"Total humans detected: {stats['class_counts'].get('person', 0)}")
```

### Pattern 4: Find Only Humans
```python
from yolov8n_scripts_improved import HUMAN_CLASSES, detect_specific_objects

# This filters to ONLY humans
detect_specific_objects('crowd.jpg', target_classes=HUMAN_CLASSES)
```

---

## Performance Tips

### Speed Up Detection
```python
# Increase confidence threshold (fewer boxes = faster)
webcam_detection(conf=0.7)  # Skip weak detections

# Lower FPS on slower hardware
webcam_detection(fps_limit=10)  # Process fewer frames
```

### For Raspberry Pi / Jetson Nano
```python
# Mobile optimized: low FPS, high confidence
webcam_detection(conf=0.6, fps_limit=5)
```

---

## Troubleshooting

### Issue: "Model not found" or slow download
**Solution**: Pre-download model
```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Issue: Low detection accuracy
**Solution**: Lower confidence threshold
```python
detect_objects_in_image('photo.jpg', conf=0.3)  # More detections but more false positives
```

### Issue: Too many false positives
**Solution**: Raise confidence threshold
```python
detect_objects_in_image('photo.jpg', conf=0.7)  # Fewer but more reliable detections
```

### Issue: Out of memory on GPU
**Solution**: Use CPU instead (slower but works on any machine)
```python
model = YOLO('yolov8n.pt')
model.info()  # Verify model loaded
# All inference will automatically use CPU if not enough GPU memory
```

---

## Integration with Navigation App

These scripts can power the navigation app's object detection:

```python
# In Flask backend (unified_server.py)
from yolov8n_scripts_improved import ObjectAnalyzer

analyzer = ObjectAnalyzer()
results = analyzer.analyze_image(frame_from_camera)

# Returns statistics for API response
```

---

## Next Steps

1. **Try Script 1** — Annotate a test image
2. **Try Script 2** — Run webcam detection
3. **Try Script 4** — Analyze a video, collect stats
4. **Customize** — Modify target classes for your use case
5. **Integrate** — Use analysis in your Flask backend or Flutter app

---

## Reference

- **YOLO Official Docs**: https://docs.ultralytics.com/models/yolov8/
- **COCO Dataset Classes**: 80 classes (person, car, dog, cat, ... bottle, etc.)
- **Model Size**: ~6.3 MB for YOLOv8n
- **Speed**: ~5-10ms per frame on modern GPU, ~50-100ms on CPU

