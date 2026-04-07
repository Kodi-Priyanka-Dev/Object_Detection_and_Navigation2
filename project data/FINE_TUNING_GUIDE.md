# Fine-Tuning Guide: Training Custom Object Detection Model

## Overview
This guide explains how to fine-tune a YOLOv8 model on your custom dataset with overfitting prevention techniques.

---

## What is Fine-Tuning?

Fine-tuning is **transfer learning** - starting with a pretrained model and adapting it to your specific task.

### Flow:
```
Pretrained YOLOv8n (trained on millions of images)
         ↓
    Load weights
         ↓
    Point to your dataset (doors, chairs, humans, etc.)
         ↓
    Train for 50 epochs
         ↓
    Adjust 11.5M weights to detect YOUR objects
         ↓
    Best model saved (best_model/best.pt)
```

---

## How Fine-Tuning Works (Step-by-Step)

### Step 1: Load Pretrained Model
```python
model = YOLO("yolov8n.pt")  # 11.5M parameters already trained
```
- Model knows basic features (edges, shapes, objects)
- Much faster than training from scratch
- Requires fewer images

### Step 2: For Each Epoch (50 times)
```
For each image in your dataset:
  1. Forward Pass: Image → Conv layers → Prediction
  2. Calculate Loss: How wrong is the prediction?
  3. Backpropagation: Calculate gradients (how to fix weights)
  4. Update Weights: Adjust all 11.5M parameters slightly
  5. Repeat for next image
```

### Step 3: Monitor Validation
```
Epoch 1:  train_loss=2.5  |  val_loss=2.6  ✅ Similar (good)
Epoch 10: train_loss=0.8  |  val_loss=1.2  ⚠️  Gap increasing
Epoch 20: train_loss=0.2  |  val_loss=2.0  ❌ Overfitting!
```

---

## Dataset Structure (REQUIRED)

```
dataset/
├── data.yaml              # Classes and paths
├── train/
│   ├── images/           # 70-80% of your images
│   └── labels/           # Corresponding .txt labels
├── valid/
│   ├── images/           # 10-15% of your images
│   └── labels/           # Corresponding .txt labels
└── test/
    ├── images/           # 10-15% of your images
    └── labels/           # Corresponding .txt labels
```

### data.yaml Format:
```yaml
train: train/images
val: valid/images
test: test/images

nc: 20  # Number of classes
names:
  0: Digital Board
  1: Door
  2: Glass Door
  3: Machine
  4: Table
  5: chair
  # ... etc
```

---

## Overfitting Prevention Techniques

### 1. **Data Augmentation** ✅
Automatically modifies images during training to create variations:
- Random rotations (±10°)
- Flips (horizontal/vertical)
- Brightness & contrast changes
- Mosaic mixing (combines 4 images)

**Enabled by default** in ultralytics.

### 2. **Train/Valid/Test Split** ✅
- **Train (70-80%)**: Used to adjust weights
- **Valid (10-15%)**: Used to detect overfitting
- **Test (10-15%)**: Final evaluation (never seen during training)

**Critical:** Never train on validation/test data!

### 3. **Early Stopping** ✅
Stop training if validation loss doesn't improve for N epochs.
```python
patience=15  # Stop if no improvement for 15 epochs
```

### 4. **Weight Decay (L2 Regularization)** ✅
Penalizes large weights, forces model to use simple solutions.
```python
weight_decay=0.0005
```

### 5. **Dropout** ✅
Randomly disables neurons during training, prevents over-reliance on specific features.
```python
dropout=0.3  # 30% of neurons disabled
```

### 6. **Batch Size** ✅
Smaller batches = more noise = better generalization.
```python
batch=16  # Good balance
```

### 7. **Learning Rate Scheduling** ✅
Gradually decrease learning rate to fine-tune weights.
```python
lr0=0.01    # Initial learning rate
lrf=0.1     # Final learning rate (lr0 * lrf)
```

### 8. **Monitoring Metrics** ✅
Watch these files in `runs/detect/detect/results.csv`:
- `box_loss`: Bounding box accuracy
- `cls_loss`: Class prediction accuracy
- `dfl_loss`: Distribution loss
- Compare `train_loss` vs `val_loss`

---

## Red Flags (Signs of Overfitting)

| Metric | Overfitting | Underfitting |
|--------|------------|---------------|
| train_loss | 0.2 (very low) | 2.0 (high) |
| val_loss | 2.0 (high) | 1.8 (high) |
| Gap (val - train) | > 1.0 ❌ | < 0.2 ✅ |
| Accuracy | High on train, Low on test | Low everywhere |

### If Overfitting Detected:
1. Increase `patience` (20 instead of 15)
2. Increase `weight_decay` (0.001 instead of 0.0005)
3. Reduce `batch` size (8 instead of 16)
4. Add more training images
5. Increase `dropout` (0.5 instead of 0.3)
6. Reduce `epochs` (30 instead of 50)

---

## Model Architecture (YOLOv8n)

You're NOT writing Conv layers - ultralytics provides them!

### Files (in .venv/Lib/site-packages/ultralytics/):
- `nn/modules/conv.py` - Conv2d layers with batch norm
- `nn/modules/block.py` - Sequential blocks
- `nn/modules/head.py` - Detection head
- `models/yolo/model.py` - Full YOLOv8 architecture

### What Happens:
```
Image (640×640×3)
  ↓
Backbone Conv Layers: Extract features (edges, shapes)
  ↓
Neck Conv Layers: Fuse features
  ↓
Head Conv Layers: Predict (x, y, w, h, confidence, class)
  ↓
Output: Detections
```

### What Changes During Fine-Tuning:
- ❌ NOT architecture (same number of layers)
- ❌ NOT general knowledge (pretraining preserved)
- ✅ YES weight values (11.5M numbers adjusted)
- ✅ YES can now detect YOUR specific 20 classes

---

## Training Checklist

Before running training, verify:

- [ ] Dataset folder structure exists
- [ ] data.yaml file created with correct paths
- [ ] Images in train/valid/test splits (70/15/15)
- [ ] Labels (.txt files) in corresponding label folders
- [ ] Minimum 100-200 images per class
- [ ] All images have labels
- [ ] No corrupted files

---

## Metrics Explained

### Loss Functions (Lower is Better):
```
box_loss:    How accurate are the bounding boxes?
cls_loss:    How well does the model classify objects?
dfl_loss:    Distribution focal loss (object vs background)
```

### Accuracy Metrics:
```
mAP50:       Mean Average Precision at IoU threshold 0.5
mAP50-95:    Mean Average Precision at 0.5-0.95 IoU
precision:   Of detected objects, how many are correct?
recall:      Of actual objects, how many did we detect?
```

---

## Files Used

**Training Script:**
- `train3.py` - Improved training with overfitting prevention

**Model:**
- `best_model/best.pt` - Your fine-tuned model

**Dataset:**
- `dataset/data.yaml` - Dataset configuration
- `dataset/train/images/` - Training images
- `dataset/valid/images/` - Validation images
- `dataset/test/images/` - Test images

**Output:**
- `runs/detect/detect/weights/best.pt` - Best weights from training
- `runs/detect/detect/results.csv` - Training metrics

---

## Next Steps

1. Prepare your dataset (images + labels)
2. Create proper train/valid/test splits
3. Run `train3.py` to start fine-tuning
4. Monitor `runs/detect/detect/results.csv`
5. Copy best model: `best_model/best.pt`
6. Start backend: `python backend_service.py`
7. Run Flutter app and test detections

---

## Common Issues & Solutions

### Issue: "No labels found"
**Solution:** Ensure `.txt` label files are in the same folder as images with same name.
```
Images: dataset/train/images/image1.jpg
Labels: dataset/train/labels/image1.txt
```

### Issue: "Bad loss or NaN"
**Solution:** 
- Check image/label alignment
- Verify label format (class x_center y_center width height, normalized)
- Try reducing learning rate

### Issue: "Running out of memory"
**Solution:** 
- Reduce batch size (16 → 8)
- Reduce image size (640 → 512)
- Reduce epochs

### Issue: Model overfitting
**Solution:** See overfitting prevention section above

---

## References

- YOLOv8 Documentation: https://docs.ultralytics.com/
- Transfer Learning: https://en.wikipedia.org/wiki/Transfer_learning
- Overfitting Prevention: https://machinelearningmastery.com/overfitting-and-underfitting/

---

**Happy Training! 🚀**
