# YOLOv8n Quick Start Guide

## 🚀 Installation (2 minutes)

```bash
# Create a virtual environment (recommended)
python -m venv yolo_env
source yolo_env/bin/activate  # On Windows: yolo_env\Scripts\activate

# Install required packages
pip install ultralytics opencv-python numpy pillow
```

## ✅ Verify Installation

```python
from ultralytics import YOLO
import cv2

# Test YOLOv8n
model = YOLO('yolov8n.pt')
print("✓ YOLOv8n loaded successfully!")
```

---

## 📋 5-Minute Implementation Examples

### 1️⃣ Detect Objects in Image

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model.predict('image.jpg', conf=0.5)

# Display results
for result in results:
    result.show()  # Open image viewer
    result.save(filename='result.jpg')  # Save annotated image
```

### 2️⃣ Real-time Webcam

```python
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture(0)  # Webcam

while True:
    ret, frame = cap.read()
    if not ret: break
    
    results = model(frame)
    annotated = results[0].plot()
    
    cv2.imshow('Detection', annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### 3️⃣ Process Video

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# Process video
results = model.predict(
    source='video.mp4',
    conf=0.5,
    save=True  # Auto-saves with annotations
)
```

---

## 🎯 Common Tasks

### Extract Detection Details

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model('image.jpg')

for result in results:
    for box in result.boxes:
        # Coordinates
        x1, y1, x2, y2 = box.xyxy[0]
        
        # Class info
        class_id = int(box.cls[0])
        class_name = result.names[class_id]
        
        # Confidence
        confidence = float(box.conf[0])
        
        print(f"{class_name}: {confidence:.2f} - Box: ({x1},{y1},{x2},{y2})")
```

### Count Objects by Type

```python
from ultralytics import YOLO
from collections import Counter

model = YOLO('yolov8n.pt')
results = model('image.jpg')

class_names = []
for result in results:
    for box in result.boxes:
        class_id = int(box.cls[0])
        class_name = result.names[class_id]
        class_names.append(class_name)

counts = Counter(class_names)
for class_name, count in counts.items():
    print(f"{class_name}: {count}")
```

### Filter by Class

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model('image.jpg')

# Only get 'person' detections
for result in results:
    persons = [box for box in result.boxes 
               if result.names[int(box.cls[0])] == 'person']
    print(f"Found {len(persons)} persons")
```

### Adjust Confidence Threshold

```python
# Strict detection (fewer false positives)
results_strict = model('image.jpg', conf=0.7)

# Lenient detection (catch more objects)
results_lenient = model('image.jpg', conf=0.3)
```

---

## ⚙️ Model Selection

```python
from ultralytics import YOLO

# Choose based on your needs:

# Fastest (real-time, edge devices)
model = YOLO('yolov8n.pt')  # Nano - 6.2 MB

# Balanced (good for most tasks)
model = YOLO('yolov8s.pt')  # Small - 22 MB
model = YOLO('yolov8m.pt')  # Medium - 49 MB

# Most Accurate (slower, powerful GPU needed)
model = YOLO('yolov8l.pt')  # Large - 83 MB
model = YOLO('yolov8x.pt')  # Extra Large - 130 MB
```

---

## 🖥️ Performance Tips

### Use GPU

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# Auto-detect GPU
results = model('image.jpg', device=0)

# Or explicit CPU
results = model('image.jpg', device='cpu')
```

### Reduce Image Size (Faster Processing)

```python
# Default 640x640
results = model('image.jpg', imgsz=640)

# Smaller size = faster, less accurate
results = model('image.jpg', imgsz=320)
```

### Batch Processing

```python
from pathlib import Path

# Process multiple images efficiently
image_folder = Path('images')
images = list(image_folder.glob('*.jpg'))

# Batch processing (faster than one-by-one)
results = model.predict(source=images, batch_size=32)
```

---

## 📊 Batch Processing Example

```python
from ultralytics import YOLO
from pathlib import Path

model = YOLO('yolov8n.pt')

# Get all images
image_dir = Path('images_folder')
images = list(image_dir.glob('*.jpg'))

print(f"Processing {len(images)} images...")

# Process all at once
results = model.predict(
    source=images,
    conf=0.5,
    batch_size=16,  # Process 16 images at once
    save=True       # Save results
)

print(f"Done! Results saved to runs/detect/predict/")
```

---

## 🐛 Troubleshooting

### Model Won't Download

```python
# The model downloads automatically on first use
# If it fails, try:
import urllib.request
from pathlib import Path

# Manually download from Ultralytics
model_url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
model_path = Path.home() / '.yolov8' / 'weights' / 'yolov8n.pt'
model_path.parent.mkdir(parents=True, exist_ok=True)

# Then use the model
from ultralytics import YOLO
model = YOLO(str(model_path))
```

### GPU Not Being Used

```python
# Check GPU availability
import torch
print("GPU Available:", torch.cuda.is_available())
print("GPU Name:", torch.cuda.get_device_name(0))

# If no GPU, use CPU explicitly
results = model('image.jpg', device='cpu')
```

### Slow Inference

```python
# Use nano model + smaller image size + GPU
model = YOLO('yolov8n.pt')
results = model('image.jpg', imgsz=320, device=0)
```

### Memory Error

```python
# Reduce batch size or use smaller model
results = model.predict(source=images, batch_size=4)  # Reduce batch

# Or use nano model
model = YOLO('yolov8n.pt')
```

---

## 📚 Important Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `conf` | 0.25 | Confidence threshold (0-1) |
| `iou` | 0.45 | IoU threshold for NMS |
| `imgsz` | 640 | Image size for inference |
| `device` | 0 | GPU device ID or 'cpu' |
| `batch_size` | 16 | Batch size for inference |
| `save` | False | Save annotated results |
| `classes` | None | Filter by class IDs |

---

## 🎓 Next Steps

1. **Try the examples**: Run the 5-minute examples above
2. **Integrate into your project**: Use the yolov8n_scripts.py file
3. **Customize**: Adjust confidence, image size, model size
4. **Optimize**: Use GPU, batch processing for speed
5. **Train custom model**: If you need domain-specific detection

---

## 📖 Useful Resources

- **Official Docs**: https://docs.ultralytics.com
- **GitHub**: https://github.com/ultralytics/ultralytics
- **YOLOv8 Models**: https://hub.ultralytics.com

---

## 🔥 Pro Tips

✨ **Tip 1**: YOLOv8n is fastest - use for real-time applications
✨ **Tip 2**: Always adjust `conf` threshold for your use case
✨ **Tip 3**: Use GPU for videos, CPU is fine for single images
✨ **Tip 4**: Smaller `imgsz` = faster but less accurate
✨ **Tip 5**: Batch processing is much faster than processing one-by-one

---

Happy detecting! 🎉
