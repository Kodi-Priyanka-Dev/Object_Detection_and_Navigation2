"""
Quick YOLOv8n to TFLite Converter
Converts yolov8n.pt to yolov8n.tflite for Flutter integration
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
import tensorflow as tf

# Paths
YOLOV8N_PATH = Path(__file__).parent / "models" / "yolov8n.pt"
OUTPUT_DIR = Path(__file__).parent / "models" / "tflite_model"
FLUTTER_ASSETS = Path(__file__).parent.parent / "Navigation App" / "assets" / "models"

print("=" * 60)
print("🔄 Converting YOLOv8n to TFLite for Flutter")
print("=" * 60)

# Verify input exists
if not YOLOV8N_PATH.exists():
    print(f"❌ ERROR: {YOLOV8N_PATH} not found")
    sys.exit(1)

print(f"\n✓ Input model: {YOLOV8N_PATH}")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    # Load model
    print(f"\n📥 Loading YOLOv8n...")
    model = YOLO(str(YOLOV8N_PATH))
    print("✓ Model loaded successfully")
    
    # Export to TFLite
    print(f"\n🔄 Exporting to TFLite...")
    export_result = model.export(
        format='tflite',
        imgsz=416,
        half=False,
        dynamic=False,
        simplify=False
    )
    
    tflite_path = Path(export_result)
    print(f"✓ Exported: {tflite_path}")
    
    # Verify
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    print("✓ Model verified successfully")
    
    # Copy to Flutter assets
    FLUTTER_ASSETS.mkdir(parents=True, exist_ok=True)
    flutter_model = FLUTTER_ASSETS / "yolov8n.tflite"
    
    import shutil
    shutil.copy2(str(tflite_path), str(flutter_model))
    
    size_mb = flutter_model.stat().st_size / (1024 * 1024)
    
    print(f"\n✅ SUCCESS!")
    print(f"   Output: {flutter_model}")
    print(f"   Size: {size_mb:.2f} MB")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
