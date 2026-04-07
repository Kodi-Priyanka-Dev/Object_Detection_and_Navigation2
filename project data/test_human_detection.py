"""
Test human detection directly with the model
Helps diagnose why humans aren't being detected in the backend
"""

import cv2
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import torch
    from ultralytics import YOLO
    import numpy as np
except Exception as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip install torch ultralytics opencv-python")
    exit(1)

# Model path
MODEL_PATH = os.path.join("best_model", "best.pt")
if not os.path.exists(MODEL_PATH):
    print(f"❌ Model not found at {MODEL_PATH}")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Looking for: {os.path.abspath(MODEL_PATH)}")
    exit(1)

print("="*70)
print("🧪 HUMAN DETECTION TEST SUITE")
print("="*70)

# Load model
print("\n[1/4] Loading YOLOv8NANO model...")
try:
    model = YOLO(MODEL_PATH)
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if str(device).startswith('cuda'):
        model.to(device)
    print(f"✅ Model loaded on device: {device}")
    print(f"   Classes: {len(model.names)} total")
except Exception as e:
    print(f"❌ Model load error: {e}")
    exit(1)

# Show all classes
print("\n[2/4] Model classes:")
for idx, cls_name in model.names.items():
    human_mark = " 👤" if cls_name.lower() in ["human", "humans", "person"] else ""
    print(f"   {idx:2d}: {cls_name}{human_mark}")

# Test webcam
print("\n[3/4] Starting webcam test (Press 'q' to quit)...")
print("      Point camera at a person and see if it detects humans")
print("      Check the confidence values - if < 0.35, threshold is issue")
print("      If no detections at all, model hasn't learned humans well")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open webcam")
    exit(1)

# Set resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_count = 0
human_frames = 0
max_human_conf = 0.0
human_detections_all = []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Skip frames for performance
    if frame_count % 2 != 0:
        continue
    
    # Run inference with very low threshold to see ALL detections
    results = model(frame, conf=0.01, device=device)  # Show even low-confidence detections
    
    # Draw detections
    output_frame = frame.copy()
    
    h, w = frame.shape[:2]
    human_found_this_frame = False
    
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])
            
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Highlight humans in RED box
            if cls_name.lower() in ["human", "humans", "person"]:
                color = (0, 0, 255)  # Red for humans
                human_found_this_frame = True
                human_detections_all.append({
                    'class': cls_name,
                    'conf': conf,
                    'frame': frame_count
                })
                if conf > max_human_conf:
                    max_human_conf = conf
            else:
                color = (0, 255, 0)  # Green for others
            
            # Draw box
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{cls_name}: {conf:.3f}"
            text_bg_color = color
            cv2.putText(output_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_bg_color, 2)
    
    if human_found_this_frame:
        human_frames += 1
    
    # Draw info
    info_text = f"Frames: {frame_count} | Humans: {len([d for d in human_detections_all])} | Max conf: {max_human_conf:.3f}"
    cv2.putText(output_frame, info_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow('Human Detection Test', output_frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Summary
print("\n[4/4] Test Results:")
print("="*70)
print(f"Total frames processed: {frame_count}")
print(f"Frames with humans detected: {human_frames}")
if human_frames > 0:
    print(f"✅ GOOD: Model CAN detect humans")
    print(f"   Max confidence found: {max_human_conf:.3f}")
    print(f"   Total human detections: {len(human_detections_all)}")
    
    if max_human_conf < 0.35:
        print(f"   ⚠️  WARNING: Max confidence ({max_human_conf:.3f}) < threshold (0.35)")
        print(f"       → You need to lower the threshold more")
        print(f"       → Or collect more diverse human training data")
    else:
        print(f"   ✅ Confidence is above threshold - should work")
else:
    print(f"❌ PROBLEM: Model NOT detecting any humans")
    print(f"   Possible causes:")
    print(f"   1. Not enough human data in training")
    print(f"   2. Humans in training data look very different")
    print(f"   3. Model file is corrupted - try retraining")
    print(f"   4. Camera resolution/quality issue")

print("="*70)
print("\n💡 NEXT STEPS:")
if human_frames == 0:
    print("   1. Try with a better quality camera or different lighting")
    print("   2. Check if best_model/best.pt is the correct trained model")
    print("   3. Consider retraining with more human images from Roboflow")
else:
    print("   1. Backend should now detect humans with updated thresholds")
    print("   2. If still not working, check image preprocessing in Flutter app")
    print("   3. Ensure JPEG quality is high enough (80% minimum)")
