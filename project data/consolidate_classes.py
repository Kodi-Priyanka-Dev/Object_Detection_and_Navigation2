"""
Consolidate duplicate classes in YOLO dataset
- Merge "chair" (5) + "chairs" (6) → "chair" (5)
- Merge "human" (8) + "humans" (9) → "human" (8)
Result: 20 classes → 18 classes
"""

import os
from pathlib import Path
import shutil

# Define class remapping
CLASS_REMAPPING = {
    # 0-5 stay the same
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
    # Remove duplicate classes
    6: 5,    # chairs → chair
    7: 6,    # flowervase
    8: 8,    # human (unchanged)
    9: 8,    # humans → human
    10: 7,   # round chair
    11: 9,   # sofa
    12: 10,  # stand
    13: 11,  # wall
    14: 12,  # wall corner
    15: 13,  # wall edge
    16: 14,  # water filter
    17: 15,  # window
    18: 16,  # wooden entrance
    19: 17,  # wooden stand
}

NEW_CLASSES = {
    0: "Digital Board",
    1: "Door",
    2: "Glass Door",
    3: "Machine",
    4: "Table",
    5: "chair",        # consolidated
    6: "flowervase",
    7: "round chair",
    8: "human",        # consolidated
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

def process_label_file(label_path):
    """Convert class indices in a label file"""
    if not os.path.exists(label_path):
        return 0
    
    try:
        with open(label_path, 'r') as f:
            lines = f.readlines()
    except:
        return 0
    
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) > 0:
            try:
                old_class = int(parts[0])
                new_class = CLASS_REMAPPING.get(old_class, old_class)
                # Reconstruct line with new class index
                new_line = f"{new_class} " + " ".join(parts[1:]) + "\n"
                new_lines.append(new_line)
            except (ValueError, IndexError):
                # If can't parse, keep original line
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write updated content back
    try:
        with open(label_path, 'w') as f:
            f.writelines(new_lines)
        return len([l for l in new_lines if l.strip()])
    except:
        return 0

def consolidate_dataset(dataset_path):
    """Process all label files in dataset"""
    dataset_path = Path(dataset_path)
    
    folders_to_process = [
        dataset_path / "train" / "labels",
        dataset_path / "valid" / "labels",
        dataset_path / "test" / "labels",
    ]
    
    total_files = 0
    total_labels = 0
    
    for folder in folders_to_process:
        if not folder.exists():
            print(f"⚠️  Folder not found: {folder}")
            continue
        
        print(f"\n📁 Processing: {folder.name}")
        label_files = list(folder.glob("*.txt"))
        
        for label_file in label_files:
            num_labels = process_label_file(label_file)
            if num_labels:
                total_files += 1
                total_labels += num_labels
                # print(f"   ✓ {label_file.name}: {num_labels} labels")
    
    return total_files, total_labels

def update_data_yaml(data_yaml_path):
    """Update data.yaml with new class definitions"""
    yaml_content = f"""train: train/images
val: valid/images
test: test/images

nc: 18
names: 
"""
    for class_id, class_name in NEW_CLASSES.items():
        yaml_content += f"  {class_id}: {class_name}\n"
    
    with open(data_yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"✓ Updated data.yaml with 18 classes (was 20)")

def main():
    dataset_path = Path("dataset")
    data_yaml_path = dataset_path / "data.yaml"
    
    print("=" * 60)
    print("CONSOLIDATING DUPLICATE CLASSES")
    print("=" * 60)
    
    print("\n📋 Class Consolidation Mapping:")
    print("   • chairs (6) → chair (5)")
    print("   • humans (9) → human (8)")
    print("   • Result: 20 classes → 18 classes")
    
    print("\n🔄 Processing label files...")
    total_files, total_labels = consolidate_dataset(dataset_path)
    
    print(f"\n✓ Processed {total_files} label files with {total_labels} total labels")
    
    print("\n📝 Updating data.yaml...")
    update_data_yaml(data_yaml_path)
    
    print("\n" + "=" * 60)
    print("✅ CONSOLIDATION COMPLETE!")
    print("=" * 60)
    print("\n📊 New Class Structure (18 classes):")
    for class_id, class_name in NEW_CLASSES.items():
        print(f"   {class_id:2d}: {class_name}")
    print("\n⏭️  Next steps:")
    print("   1. Retrain model with: python train3.py or python train_yolov8l.py")
    print("   2. Update backend_service.py class references")

if __name__ == "__main__":
    main()
