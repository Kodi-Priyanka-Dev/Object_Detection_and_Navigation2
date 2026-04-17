# YOLOv8n Implementation Guide

## 1. Installation & Setup

### Install Required Libraries
```bash
# Install YOLOv8
pip install ultralytics

# Install supporting libraries
pip install opencv-python
pip install numpy
pip install pillow
```

### Verify Installation
```python
from ultralytics import YOLO
print("YOLOv8 installed successfully!")
```

---

## 2. Basic YOLOv8n Implementation

### Simple Image Detection
```python
from ultralytics import YOLO
from PIL import Image
import cv2

# Load the YOLOv8n model (nano version - fastest)
model = YOLO('yolov8n.pt')

# Perform inference on an image
results = model.predict(source='path/to/image.jpg', conf=0.5)

# Display results
for result in results:
    print(result.boxes)  # Object detection boxes
    # Save image with detections
    result.save(filename='result.jpg')
```

---

## 3. Real-time Video Detection

### Process Video File
```python
from ultralytics import YOLO
import cv2

# Load model
model = YOLO('yolov8n.pt')

# Open video file
video_path = 'path/to/video.mp4'
cap = cv2.VideoCapture(video_path)

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run YOLOv8 inference
    results = model(frame)
    
    # Visualize results on frame
    annotated_frame = results[0].plot()
    
    # Write frame to output video
    out.write(annotated_frame)
    
    frame_count += 1
    if frame_count % 30 == 0:
        print(f"Processed {frame_count} frames")

cap.release()
out.release()
print("Video processing complete!")
```

### Real-time Webcam Detection
```python
from ultralytics import YOLO
import cv2

# Load model
model = YOLO('yolov8n.pt')

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run inference
    results = model(frame, conf=0.5)
    
    # Annotate frame
    annotated_frame = results[0].plot()
    
    # Display frame
    cv2.imshow('YOLOv8n Detection', annotated_frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## 4. Advanced Features

### Extract Detailed Information
```python
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')
results = model('image.jpg')

for result in results:
    # Get boxes with coordinates
    boxes = result.boxes
    
    for box in boxes:
        # Bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0]
        
        # Confidence score
        conf = box.conf[0]
        
        # Class ID and name
        cls = int(box.cls[0])
        cls_name = result.names[cls]
        
        print(f"Class: {cls_name}, Confidence: {conf:.2f}")
        print(f"Box: ({x1}, {y1}, {x2}, {y2})")
```

### Filter Detections by Class
```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model('image.jpg')

# Filter only 'person' and 'car' detections
target_classes = ['person', 'car']

for result in results:
    boxes = result.boxes
    for box in boxes:
        cls_name = result.names[int(box.cls[0])]
        if cls_name in target_classes:
            print(f"Detected: {cls_name}")
```

### Custom Confidence Threshold
```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# Set different confidence thresholds
results_high_conf = model('image.jpg', conf=0.7)  # Strict
results_low_conf = model('image.jpg', conf=0.3)   # Lenient
```

---

## 5. Performance Optimization

### Model Variants (Speed vs Accuracy)
```
YOLOv8n  - Nano (fastest, least accurate)
YOLOv8s  - Small
YOLOv8m  - Medium
YOLOv8l  - Large
YOLOv8x  - Extra Large (slowest, most accurate)
```

### Use GPU for Faster Inference
```python
from ultralytics import YOLO

# Auto-detect GPU (if available)
model = YOLO('yolov8n.pt')
results = model('image.jpg', device=0)  # device=0 for GPU, device='cpu' for CPU
```

### Batch Processing
```python
from ultralytics import YOLO
from pathlib import Path

model = YOLO('yolov8n.pt')

# Process multiple images at once (faster)
image_dir = Path('path/to/images')
image_paths = list(image_dir.glob('*.jpg'))

results = model.predict(source=image_paths, conf=0.5, batch_size=32)
```

---

## 6. Training on Custom Dataset

### Prepare Dataset Structure
```
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### Create dataset.yaml
```yaml
path: /path/to/dataset
train: images/train
val: images/val
test: images/test
nc: 2  # number of classes
names: ['class1', 'class2']
```

### Train Custom Model
```python
from ultralytics import YOLO

# Load a pretrained model
model = YOLO('yolov8n.pt')

# Train the model
results = model.train(
    data='path/to/dataset.yaml',
    epochs=100,
    imgsz=640,
    device=0,  # GPU device
    batch=16,
    patience=20,  # Early stopping
    save=True
)
```

---

## 7. Complete Example Project

### Object Counter
```python
from ultralytics import YOLO
import cv2
from collections import defaultdict

class ObjectCounter:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        self.class_counts = defaultdict(int)
    
    def process_frame(self, frame):
        results = self.model(frame)
        
        # Reset counts
        self.class_counts.clear()
        
        # Count objects
        for result in results:
            for box in result.boxes:
                cls_name = result.names[int(box.cls[0])]
                self.class_counts[cls_name] += 1
        
        # Annotate frame
        annotated_frame = results[0].plot()
        
        # Add text with counts
        y_offset = 30
        for cls_name, count in self.class_counts.items():
            text = f"{cls_name}: {count}"
            cv2.putText(annotated_frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30
        
        return annotated_frame
    
    def process_video(self, video_path, output_path='output.mp4'):
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            annotated_frame = self.process_frame(frame)
            out.write(annotated_frame)
        
        cap.release()
        out.release()
        print(f"Output saved to {output_path}")

# Usage
counter = ObjectCounter()
counter.process_video('input_video.mp4')
```

---

## 8. Model Download

The first time you use a model, it will be automatically downloaded (~6.2 MB for YOLOv8n).

Downloaded models are stored in: `~/.yolov8/weights/`

To manually download:
```python
from ultralytics import YOLO

# This will download and cache the model
model = YOLO('yolov8n.pt')
```

---

## 9. Troubleshooting

### Common Issues

**Issue: Model download fails**
```python
# Manually specify weights path
model = YOLO('yolov8n.pt')  # Will download automatically
# Or use full path if downloaded manually
```

**Issue: GPU not being used**
```python
# Check GPU availability
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Use CPU explicitly if GPU not available
model = YOLO('yolov8n.pt')
results = model('image.jpg', device='cpu')
```

**Issue: Slow inference**
```python
# Use faster model or reduce image size
model = YOLO('yolov8n.pt')
results = model('image.jpg', imgsz=320)  # Smaller size = faster
```

---

## 10. Key Methods & Parameters

### Prediction Methods
```python
model.predict()   # Run inference
model.train()     # Train on dataset
model.val()       # Validate on dataset
model.export()    # Export model to different format
model.benchmark() # Benchmark model
```

### Common Parameters
- `conf`: Confidence threshold (0-1)
- `iou`: IoU threshold for NMS
- `imgsz`: Image size for inference
- `device`: GPU/CPU device
- `batch_size`: Batch size for processing
- `save`: Save results
- `classes`: Filter by specific class IDs

---

## Summary

1. **Install**: `pip install ultralytics opencv-python`
2. **Load Model**: `model = YOLO('yolov8n.pt')`
3. **Predict**: `results = model.predict(source='image.jpg')`
4. **Process Results**: Extract boxes, classes, confidence scores
5. **Optimize**: Choose right model size, use GPU, adjust parameters

**YOLOv8n is ideal for:**
- ✅ Real-time applications (fast inference)
- ✅ Edge devices (low memory)
- ✅ CPU-only systems
- ❌ Accuracy-critical tasks (use larger models)
