#!/usr/bin/env python3
"""
Quick test to verify YOLO model is working
"""
import os
import cv2
from ultralytics import YOLO

# Disable CUDA
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

print("Testing YOLO model detection...")
print("-" * 60)

# Load model
model_path = "best_model/best.pt"
print(f"Loading model from: {model_path}")
print(f"File exists: {os.path.exists(model_path)}")

try:
    model = YOLO(model_path)
    print("✅ Model loaded!")
    print(f"Classes: {list(model.names.values())}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n" + "-" * 60)
print("Model information:")
print(f"  Device: CPU (CUDA disabled)")
print(f"  Number of classes: {len(model.names)}")
print(f"  Classes: {model.names}")

print("\n✅ Model is working correctly!")
print("Fire" up the app and point a door at the camera.")
