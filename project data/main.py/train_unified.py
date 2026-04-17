"""
Unified Model Training Script (YOLOv8s)
==========================================
Downloads COCO images for missing classes (person, backpack, handbag, suitcase, bottle, couch)
and merges them with your existing custom dataset, then trains ONE YOLOv8s model that detects everything.

Model: YOLOv8s (Small - 11.2M parameters, 22MB)
  ✓ Better accuracy than YOLOv8n (+6%)
  ✓ Still fast inference (~8ms/frame)
  ✓ Good balance for mobile + backend deployment

Final model: unified_model/best.pt
Classes: 20 custom + 6 COCO = 26 total

Usage:
    python train_unified.py
"""

import os
import sys
import shutil
import yaml
import random
import torch
from pathlib import Path

# ─────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────
BASE_PATH = Path(os.getcwd())
ORIGINAL_DATASET = BASE_PATH / "dataset"
UNIFIED_DATASET = BASE_PATH / "dataset_unified"
TRAIN_OUTPUT = BASE_PATH / "runs"
UNIFIED_MODEL_DIR = BASE_PATH / "unified_model"

# Consolidated 18 classes (chairs→chair, humans→human)
CUSTOM_CLASSES = {
    0: "Digital Board",
    1: "Door",
    2: "Glass Door",
    3: "Machine",
    4: "Table",
    5: "chair",              # Consolidated: "chairs" merged
    6: "flowervase",
    7: "round chair",
    8: "human",              # Consolidated: "humans" merged
    9: "sofa",
    10: "stand",
    11: "wall",
    12: "wall corner",
    13: "wall edge",
    14: "water filter",
    15: "window",
    16: "wooden entrance",
    17: "wooden stand",
}

# New COCO classes to add (mapped from COCO IDs to new unified IDs)
# These are the classes from yolo26n that your custom model doesn't have
NEW_COCO_CLASSES = {
    20: "person",
    21: "backpack",
    22: "handbag",
    23: "suitcase",
    24: "bottle",
    25: "couch",
}

# COCO class ID -> Unified class ID mapping
COCO_TO_UNIFIED = {
    0: 20,    # person -> 20
    24: 21,   # backpack -> 21
    26: 22,   # handbag -> 22
    28: 23,   # suitcase -> 23
    39: 24,   # bottle -> 24
    57: 25,   # couch -> 25
}

ALL_CLASSES = {**CUSTOM_CLASSES, **NEW_COCO_CLASSES}


def step1_copy_custom_dataset():
    """Step 1: Copy existing custom dataset to unified folder"""
    print("\n" + "=" * 60)
    print("STEP 1: Copying custom dataset to unified folder")
    print("=" * 60)

    for split in ["train", "valid", "test"]:
        for subdir in ["images", "labels"]:
            src = ORIGINAL_DATASET / split / subdir
            dst = UNIFIED_DATASET / split / subdir
            dst.mkdir(parents=True, exist_ok=True)

            if not src.exists():
                print(f"  ⚠️  Skipping {src} (not found)")
                continue

            count = 0
            for f in src.iterdir():
                if f.is_file():
                    shutil.copy2(f, dst / f.name)
                    count += 1
            print(f"  ✓ Copied {count} files: {split}/{subdir}")


def step2_download_coco_subset():
    """
    Step 2: Download COCO images for missing classes using ultralytics.
    Uses the COCO128 or COCO validation set as a quick source.
    """
    print("\n" + "=" * 60)
    print("STEP 2: Downloading COCO subset for new classes")
    print("=" * 60)
    print("  Classes needed: person, backpack, handbag, suitcase, bottle, couch")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("  ❌ ultralytics not installed. Run: pip install ultralytics")
        return False

    # Use YOLOv8n pretrained to detect and filter COCO validation images
    # First, download COCO128 mini dataset (built into ultralytics)
    coco_dir = BASE_PATH / "coco_temp"
    coco_dir.mkdir(exist_ok=True)

    print("  📥 Downloading COCO128 dataset via ultralytics...")
    print("     (This is a small 128-image COCO subset for quick bootstrapping)")

    model = YOLO("yolov8s.pt")  # YOLOv8s for COCO detection (same model as training)

    # Download coco128 by running a dummy validation
    try:
        model.val(data="coco128.yaml", imgsz=640, batch=1, verbose=False, plots=False)
        print("  ✓ COCO128 downloaded")
    except Exception as e:
        print(f"  ⚠️  COCO128 auto-download issue: {e}")
        print("  → Will proceed with existing custom dataset only.")
        print("  → For best results, manually add COCO images later.")
        return False

    # Find where ultralytics downloaded coco128
    possible_paths = [
        Path.home() / "datasets" / "coco128",
        BASE_PATH / "datasets" / "coco128",
        Path("datasets") / "coco128",
    ]

    coco128_path = None
    for p in possible_paths:
        if p.exists():
            coco128_path = p
            break

    if coco128_path is None:
        print("  ⚠️  Could not find downloaded COCO128 dataset.")
        print("  → Proceeding with custom dataset only.")
        return False

    print(f"  ✓ Found COCO128 at: {coco128_path}")

    # COCO class IDs we want
    wanted_coco_ids = set(COCO_TO_UNIFIED.keys())  # {0, 24, 26, 28, 39, 57}

    # Process COCO128 labels and copy relevant images
    coco_images_dir = coco128_path / "images" / "train2017"
    coco_labels_dir = coco128_path / "labels" / "train2017"

    if not coco_images_dir.exists():
        print(f"  ⚠️  COCO128 images not found at {coco_images_dir}")
        return False

    added_count = 0

    for label_file in coco_labels_dir.glob("*.txt"):
        # Read label file and check if it contains any wanted classes
        with open(label_file, 'r') as f:
            lines = f.readlines()

        new_lines = []
        has_wanted = False

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            coco_cls_id = int(parts[0])

            if coco_cls_id in wanted_coco_ids:
                # Remap COCO class ID to unified class ID
                unified_id = COCO_TO_UNIFIED[coco_cls_id]
                new_lines.append(f"{unified_id} {' '.join(parts[1:])}\n")
                has_wanted = True

        if has_wanted:
            # Copy image
            img_name = label_file.stem
            img_file = None
            for ext in [".jpg", ".jpeg", ".png"]:
                candidate = coco_images_dir / f"{img_name}{ext}"
                if candidate.exists():
                    img_file = candidate
                    break

            if img_file:
                # Copy to unified train set with prefix to avoid name clashes
                dst_img = UNIFIED_DATASET / "train" / "images" / f"coco_{img_file.name}"
                dst_lbl = UNIFIED_DATASET / "train" / "labels" / f"coco_{label_file.name}"

                shutil.copy2(img_file, dst_img)
                with open(dst_lbl, 'w') as f:
                    f.writelines(new_lines)
                added_count += 1

    print(f"  ✓ Added {added_count} COCO images with remapped labels")

    # Also add some to validation
    val_images = list((UNIFIED_DATASET / "train" / "images").glob("coco_*"))
    val_count = min(len(val_images) // 5, 20)  # 20% to validation
    if val_count > 0:
        random.shuffle(val_images)
        for img in val_images[:val_count]:
            lbl = UNIFIED_DATASET / "train" / "labels" / (img.stem + ".txt")
            shutil.move(str(img), UNIFIED_DATASET / "valid" / "images" / img.name)
            if lbl.exists():
                shutil.move(str(lbl), UNIFIED_DATASET / "valid" / "labels" / lbl.name)
        print(f"  ✓ Moved {val_count} COCO images to validation set")

    return True


def step3_create_data_yaml():
    """Step 3: Create unified data.yaml with all 26 classes"""
    print("\n" + "=" * 60)
    print("STEP 3: Creating unified data.yaml")
    print("=" * 60)

    data_yaml = {
        "path": str(UNIFIED_DATASET.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "names": ALL_CLASSES,
    }

    yaml_path = UNIFIED_DATASET / "data.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(data_yaml, f, default_flow_style=False, sort_keys=False)

    print(f"  ✓ Created {yaml_path}")
    print(f"  ✓ Total classes: {len(ALL_CLASSES)}")
    for idx, name in ALL_CLASSES.items():
        marker = "  (NEW)" if idx >= 20 else ""
        print(f"    {idx}: {name}{marker}")


def step4_train():
    """Step 4: Train unified model with YOLOv8s"""
    print("\n" + "=" * 60)
    print("STEP 4: Training unified model (YOLOv8s)")
    print("=" * 60)

    from ultralytics import YOLO

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device: {device}")
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    yaml_path = UNIFIED_DATASET / "data.yaml"

    # Start from YOLOv8s pretrained weights (Better accuracy than YOLOv8n)
    # 11.2M parameters, 22MB model size, ~8ms inference
    model = YOLO("yolov8s.pt")

    print(f"\n  🚀 Starting YOLOv8s training...")
    print(f"  📁 Dataset: {yaml_path}")
    print(f"  📊 Classes: {len(ALL_CLASSES)} (20 custom + 6 COCO)")
    print(f"  📈 Model: YOLOv8s (Small) - 11.2M parameters")

    # Train with optimized settings for RTX A2000 12GB (YOLOv8s optimized)
    model.train(
        data=str(yaml_path),
        epochs=50,           # Reduced from 100 (YOLOv8s trains faster)
        imgsz=640,
        batch=16,            # Good balance for RTX A2000 12GB
        project=str(TRAIN_OUTPUT),
        name="unified_yolov8s",  # Separate run for YOLOv8s
        device=device,
        amp=True,            # Mixed precision training
        workers=0,           # Windows compatibility
        cache=True,          # Cache images in RAM for speed
        patience=15,         # Early stopping if no improvement for 15 epochs
        dropout=0.3,         # Overfitting prevention
        weight_decay=0.0005, # L2 regularization
        save=True,
        save_period=10,      # Save checkpoint every 10 epochs
        plots=True,
        cos_lr=True,         # Cosine learning rate scheduler
        lr0=0.01,            # Initial learning rate
        lrf=0.1,             # Final learning rate multiplier
        warmup_epochs=3,     # Less warmup needed for YOLOv8s
        close_mosaic=10,
        mosaic=1.0,          # Data augmentation via mosaic
    )

    print("\n  ✅ Training completed!")

    # Copy best model
    best_path = TRAIN_OUTPUT / "unified" / "weights" / "best.pt"
    if best_path.exists():
        UNIFIED_MODEL_DIR.mkdir(exist_ok=True)
        dst = UNIFIED_MODEL_DIR / "best.pt"
        shutil.copy2(best_path, dst)
        print(f"  ✓ Best model saved to: {dst}")
        return True
    else:
        # Check for numbered folder (unified2, unified3, etc.)
        for p in sorted(TRAIN_OUTPUT.glob("unified*/weights/best.pt"), reverse=True):
            UNIFIED_MODEL_DIR.mkdir(exist_ok=True)
            dst = UNIFIED_MODEL_DIR / "best.pt"
            shutil.copy2(p, dst)
            print(f"  ✓ Best model saved to: {dst}")
            return True

    print("  ❌ Best model not found!")
    return False


def step5_test():
    """Step 5: Quick test of the unified model"""
    print("\n" + "=" * 60)
    print("STEP 5: Testing unified model")
    print("=" * 60)

    model_path = UNIFIED_MODEL_DIR / "best.pt"
    if not model_path.exists():
        print("  ❌ Unified model not found. Training may have failed.")
        return

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    print(f"  ✓ Model loaded: {model_path}")
    print(f"  ✓ Classes: {len(model.names)}")
    for idx, name in model.names.items():
        print(f"    {idx}: {name}")

    # Validate on test set
    yaml_path = UNIFIED_DATASET / "data.yaml"
    if yaml_path.exists():
        print("\n  📊 Running validation...")
        metrics = model.val(data=str(yaml_path), imgsz=640, batch=8, verbose=False)
        print(f"  ✓ mAP50: {metrics.box.map50:.4f}")
        print(f"  ✓ mAP50-95: {metrics.box.map:.4f}")


def main():
    print("=" * 60)
    print("UNIFIED MODEL TRAINING PIPELINE")
    print("=" * 60)
    print(f"Custom dataset: {ORIGINAL_DATASET}")
    print(f"Unified dataset: {UNIFIED_DATASET}")
    print(f"Output model: {UNIFIED_MODEL_DIR / 'best.pt'}")
    print(f"GPU: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

    # Step 1: Copy existing dataset
    step1_copy_custom_dataset()

    # Step 2: Download and merge COCO subset
    coco_added = step2_download_coco_subset()
    if not coco_added:
        print("\n  ℹ️  Proceeding without COCO images.")
        print("  → Model will train on custom 20 classes only.")
        print("  → Add COCO images to dataset_unified/train/ later and retrain.")

    # Step 3: Create unified data.yaml
    step3_create_data_yaml()

    # Step 4: Train
    step4_train()

    # Step 5: Test
    step5_test()

    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"\nUnified model saved at: {UNIFIED_MODEL_DIR / 'best.pt'}")
    print("\nTo use this model in your app:")
    print("  1. Copy unified_model/best.pt to Navigation App/")
    print("  2. Update backend_service.py MODEL_PATH to point to unified model")
    print("  3. Run a single backend server - no more model switching needed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
