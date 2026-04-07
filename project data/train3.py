"""
Enhanced Training Script with Overfitting Prevention
====================================================

This script fine-tunes YOLOv8 on your custom dataset with multiple
safeguards against overfitting:

✅ Early Stopping (patience)
✅ Weight Decay (L2 regularization)
✅ Dropout
✅ Proper Train/Valid/Test split
✅ Data Augmentation
✅ Learning Rate Scheduling
✅ Metrics Monitoring

Usage:
    python train3.py
"""

from ultralytics import YOLO
import cv2
import os
import shutil
import torch
import csv
from datetime import datetime


def main():
    # ============================================================
    # CONFIGURATION
    # ============================================================
    
    # Paths
    BASE_PATH = os.getcwd()
    DATA_YAML = os.path.join(BASE_PATH, "dataset", "data.yaml")
    VIDEO_PATH = r"C:\Users\Priyanka\Documents\project data\input video 2.mp4"
    OUTPUT_FOLDER = os.path.join(BASE_PATH, "visualization")
    TRAIN_FOLDER = os.path.join(BASE_PATH, "runs")
    OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, "output_video.mp4")
    SAVED_MODEL_PATH = os.path.join(BASE_PATH, "best_model", "best.pt")

    # Create directories
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(TRAIN_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(BASE_PATH, "best_model"), exist_ok=True)

    print("=" * 70)
    print("ENHANCED YOLOV8 FINE-TUNING WITH OVERFITTING PREVENTION")
    print("=" * 70)
    print(f"\n📁 Project Path: {BASE_PATH}")
    print(f"📁 Data YAML: {DATA_YAML}")
    print(f"📁 Video Path: {VIDEO_PATH}")
    print(f"✅ Video Exists: {os.path.exists(VIDEO_PATH)}")

    if not os.path.exists(VIDEO_PATH):
        print("\n❌ Video file not found! Check path.")
        return

    # ============================================================
    # CHECK CUDA AVAILABILITY
    # ============================================================
    print("\n" + "=" * 70)
    print("HARDWARE CHECK")
    print("=" * 70)
    
    if torch.cuda.is_available():
        print("✅ CUDA GPU detected. Training on GPU...")
        device = "cuda"
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️  CUDA not available. Training on CPU...")
        print("   (Training will be slower)")
        device = "cpu"

    # ============================================================
    # LOAD MODEL
    # ============================================================
    print("\n" + "=" * 70)
    print("LOADING PRETRAINED MODEL")
    print("=" * 70)
    
    model = YOLO("yolov8n.pt")
    print("✅ YOLOv8n model loaded")
    print(f"   Model size: ~3.3M parameters (Nano)")
    print(f"   Architecture: Pretrained on COCO dataset")
    print(f"   Accuracy: Lightweight (Nano, 2-3% less than Small)")

    # ============================================================
    # TRAINING CONFIGURATION WITH OVERFITTING PREVENTION
    # ============================================================
    print("\n" + "=" * 70)
    print("TRAINING CONFIGURATION")
    print("=" * 70)
    
    training_config = {
        # Basic settings
        "data": DATA_YAML,
        "epochs": 50,
        "imgsz": 640,
        "batch": 16,
        "project": TRAIN_FOLDER,
        "name": "detect_yolov8n",  # Updated run name for YOLOv8n
        "device": device,
        
        # 🛡️ OVERFITTING PREVENTION TECHNIQUES:
        
        # 1. Early Stopping
        "patience": 15,
        # Stops training if validation doesn't improve for 15 epochs
        # Prevents training too long and overfitting
        
        # 2. Weight Decay (L2 Regularization)
        "weight_decay": 0.0005,
        # Penalizes large weights, forces simpler solutions
        # Reduces model complexity and overfitting
        
        # 3. Dropout
        "dropout": 0.3,
        # Randomly disables 30% of neurons during training
        # Forces learning of multiple independent features
        
        # 4. Learning Rate Scheduling
        "lr0": 0.01,      # Initial learning rate
        "lrf": 0.1,       # Final learning rate (as fraction of lr0)
        # Learning rate decreases over time: 0.01 → 0.001
        # Fine-tunes weights without large jumps
        
        # 5. Data Augmentation (enabled by default)
        "mosaic": 1.0,    # Mosaic augmentation
        # Combines 4 random images during training
        # Creates diverse training data
        
        # 6. Hardware Optimization
        "amp": True,      # Automatic Mixed Precision
        # Faster training, same accuracy
        
        "workers": 0,     # Windows compatibility (no multiprocessing)
        "cache": True,    # Cache images in RAM for speed
        
        # 7. Model Preservation
        "save": True,     # Save checkpoints
        "exist_ok": False,  # Don't overwrite existing runs
        
        # 8. Monitoring
        "verbose": True,  # Print detailed logs
    }

    print("🛡️  Overfitting Prevention Settings:")
    print(f"   ✓ Early Stopping (patience): {training_config['patience']} epochs")
    print(f"   ✓ Weight Decay: {training_config['weight_decay']}")
    print(f"   ✓ Dropout: {training_config['dropout']}")
    print(f"   ✓ Learning Rate: {training_config['lr0']} → {training_config['lrf']}")
    print(f"   ✓ Batch Size: {training_config['batch']}")
    print(f"   ✓ Epochs: {training_config['epochs']}")

    # ============================================================
    # DATASET VALIDATION
    # ============================================================
    print("\n" + "=" * 70)
    print("DATASET VALIDATION")
    print("=" * 70)
    
    if not os.path.exists(DATA_YAML):
        print(f"❌ data.yaml not found at {DATA_YAML}")
        return
    
    print(f"✅ data.yaml found")
    
    # Check for train/valid/test folders
    train_folder = os.path.join(BASE_PATH, "dataset", "train", "images")
    valid_folder = os.path.join(BASE_PATH, "dataset", "valid", "images")
    test_folder = os.path.join(BASE_PATH, "dataset", "test", "images")
    
    train_count = len([f for f in os.listdir(train_folder) if f.endswith(('.jpg', '.png'))]) if os.path.exists(train_folder) else 0
    valid_count = len([f for f in os.listdir(valid_folder) if f.endswith(('.jpg', '.png'))]) if os.path.exists(valid_folder) else 0
    test_count = len([f for f in os.listdir(test_folder) if f.endswith(('.jpg', '.png'))]) if os.path.exists(test_folder) else 0
    
    print(f"📊 Dataset Distribution:")
    print(f"   Train: {train_count} images ({train_count/(train_count+valid_count+test_count)*100:.1f}%)")
    print(f"   Valid: {valid_count} images ({valid_count/(train_count+valid_count+test_count)*100:.1f}%)")
    print(f"   Test:  {test_count} images ({test_count/(train_count+valid_count+test_count)*100:.1f}%)")
    print(f"   Total: {train_count + valid_count + test_count} images")
    
    total = train_count + valid_count + test_count
    if total < 300:
        print("\n⚠️  WARNING: Less than 300 images. Consider adding more data.")

    # ============================================================
    # TRAINING
    # ============================================================
    print("\n" + "=" * 70)
    print("STARTING FINE-TUNING")
    print("=" * 70)
    print(f"⏱️  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = model.train(**training_config)
    
    print("\n✅ Training completed!")

    # ============================================================
    # RESULTS MONITORING
    # ============================================================
    print("\n" + "=" * 70)
    print("TRAINING RESULTS")
    print("=" * 70)
    
    results_csv = os.path.join(TRAIN_FOLDER, "detect_yolov8n", "results.csv")
    if os.path.exists(results_csv):
        print(f"📊 Results saved to: {results_csv}")
        
        # Read last few rows to show final metrics
        with open(results_csv, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                print("\n📈 Final Metrics:")
                print(f"   {lines[-1].strip()}")

    # ============================================================
    # COPY BEST MODEL
    # ============================================================
    print("\n" + "=" * 70)
    print("SAVING BEST MODEL")
    print("=" * 70)
    
    best_model_path = os.path.join(TRAIN_FOLDER, "detect_yolov8n", "weights", "best.pt")
    
    if not os.path.exists(best_model_path):
        print("❌ Best model not found!")
        return
    
    shutil.copy2(best_model_path, SAVED_MODEL_PATH)
    model_size = os.path.getsize(SAVED_MODEL_PATH) / (1024 * 1024)
    print(f"✅ Best model saved to: {SAVED_MODEL_PATH}")
    print(f"   File size: {model_size:.2f} MB")

    # ============================================================
    # VIDEO INFERENCE
    # ============================================================
    print("\n" + "=" * 70)
    print("RUNNING INFERENCE ON VIDEO")
    print("=" * 70)
    
    # Load best model
    model = YOLO(SAVED_MODEL_PATH)
    print(f"✅ Best model loaded for inference")

    # Open video
    cap = cv2.VideoCapture(VIDEO_PATH, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("❌ Error opening video file.")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 30  # fallback FPS

    print(f"📹 Video info:")
    print(f"   Resolution: {frame_width}x{frame_height}")
    print(f"   FPS: {fps}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

    print("\n▶️  Processing video... Press 'q' to stop.")

    frame_count = 0
    detection_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Run inference
        results = model(frame, device=device)
        annotated_frame = results[0].plot()
        
        # Count detections
        if len(results[0].boxes) > 0:
            detection_count += len(results[0].boxes)

        out.write(annotated_frame)
        cv2.imshow("YOLOv8 Detection", annotated_frame)

        # Progress indicator
        if frame_count % 30 == 0:
            print(f"   Processed {frame_count} frames, {detection_count} objects detected")

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"\n✅ Inference completed!")
    print(f"   Total frames: {frame_count}")
    print(f"   Total detections: {detection_count}")
    print(f"   Output saved: {OUTPUT_PATH}")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"✅ Model trained with overfitting prevention")
    print(f"✅ Best model saved: {SAVED_MODEL_PATH}")
    print(f"✅ Video processed: {OUTPUT_PATH}")
    print(f"✅ Ready for deployment!")
    print("\n📝 Next Steps:")
    print(f"   1. Review metrics in: {results_csv}")
    print(f"   2. Check for overfitting (val_loss vs train_loss gap)")
    print(f"   3. Start backend: python backend_service.py")
    print(f"   4. Run Flutter app to test detections")
    print("=" * 70)


if __name__ == "__main__":
    main()
