#!/usr/bin/env python3
"""
Fix 18-Class Model - Retrain from Fresh YOLOv8n
===============================================
Trains a fresh YOLOv8n model with proper 18-class consolidation
"""

import os
import torch
from ultralytics import YOLO

print("\n" + "=" * 80)
print("🔄 RETRAINING WITH 18-CLASS CONSOLIDATION")
print("=" * 80)

# Step 1: Check GPU
print("\n[1/4] Checking GPU...")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"✅ GPU: {gpu_name} ({gpu_memory:.1f}GB)")
else:
    print("⚠️  CPU mode (will be slower)")

# Step 2: Load FRESH YOLOv8n (not the old 20-class model)
print("\n[2/4] Loading fresh YOLOv8n model...")
model = YOLO("yolov8n.pt")  # Fresh model - NOT best.pt
print("✅ Fresh YOLOv8n loaded")

# Step 3: Train on 18-class dataset
print("\n[3/4] Training with 18-class dataset...")
dataset_config = r"C:\Users\Priyanka\Documents\project data\dataset_fine_tune\data.yaml"

print(f"Dataset config: {dataset_config}")
print(f"Exists: {os.path.exists(dataset_config)}")

results = model.train(
    data=dataset_config,
    epochs=50,
    batch=64,
    imgsz=640,
    device=0,
    project="runs/detect",
    name="consolidated_18class",
    exist_ok=True,
    lr0=0.001,  # Start with normal learning rate for fresh model
    patience=15,
    save=True,
    plots=True,
    verbose=True,
    workers=8,
)

# Step 4: Deploy the corrected model
print("\n[4/4] Deploying corrected model...")
best_path = r"runs\detect\consolidated_18class\weights\best.pt"
deploy_path = r"best_model\best.pt"

if os.path.exists(best_path):
    print(f"Source: {best_path}")
    print(f"Target: {deploy_path}")
    
    # Load and verify the model
    new_model = YOLO(best_path)
    print(f"\n✅ Model Summary:")
    print(f"   Architecture: YOLOv8n")
    print(f"   Classes: {len(new_model.names)}")
    print(f"   Class names: {list(new_model.names.values())}")
    
    # Verify consolidation
    classes_list = list(new_model.names.values())
    if 'chairs' in classes_list:
        print("   ❌ WARNING: Still has 'chairs' instead of 'chair'")
    if 'humans' in classes_list:
        print("   ❌ WARNING: Still has 'humans' instead of 'human'")
    
    if len(new_model.names) == 18:
        print("   ✅ CORRECT: 18 classes")
    else:
        print(f"   ❌ WARNING: {len(new_model.names)} classes instead of 18")
    
    # Deploy
    import shutil
    shutil.copy2(best_path, deploy_path)
    print(f"\n✅ Model deployed to: {deploy_path}")
    print(f"   Size: {os.path.getsize(deploy_path) / 1e6:.1f}MB")
else:
    print(f"❌ Model not found: {best_path}")

print("\n" + "=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)
print("\nNext steps:")
print("  1. Restart backend: python Navigation App/backend_service.py")
print("  2. Test in Flutter app")
print("=" * 80 + "\n")
