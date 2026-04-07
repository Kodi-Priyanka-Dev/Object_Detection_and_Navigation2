"""
FINAL CONSOLIDATION - Complete and verified
Consolidate 20 classes → 18 classes
- chairs (6) → chair (5)
- humans (9) → human (8)
"""
import os
from pathlib import Path
import shutil

# COMPLETE mapping from 20 classes to 18 classes
CLASS_REMAPPING = {
    # Keep 0-5 unchanged
    0: 0,    # Digital Board
    1: 1,    # Door
    2: 2,    # Glass Door
    3: 3,    # Machine
    4: 4,    # Table
    5: 5,    # chair
    # Consolidate 6→5 (chairs→chair)
    6: 5,    
    # Remap 7+ down by 1
    7: 6,    # flowervase (was 7, now 6)
    8: 8,    # human (no change, but some will merge with 9)
    # Consolidate 9→8 (humans→human)
    9: 8,    
    # Remap 10+ down by 2
    10: 7,   # round chair (was 10, now 7)
    11: 9,   # sofa (was 11, now 9)
    12: 10,  # stand (was 12, now 10)
    13: 11,  # wall (was 13, now 11)
    14: 12,  # wall corner (was 14, now 12)
    15: 13,  # wall edge (was 15, now 13)
    16: 14,  # water filter (was 16, now 14)
    17: 15,  # window (was 17, now 15)
    18: 16,  # wooden entrance (was 18, now 16)
    19: 17,  # wooden stand (was 19, now 17)
}

def consolidate_file(filepath):
    """Apply consolidation to one file"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) > 0:
                try:
                    old_cls = int(parts[0])
                    new_cls = CLASS_REMAPPING[old_cls]  # Will raise KeyError if old_cls > 19
                    new_line = f"{new_cls} " + " ".join(parts[1:]) + "\n"
                    new_lines.append(new_line)
                except (ValueError, KeyError) as e:
                    # Keep original if can't parse or unknown class
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"ERROR {filepath}: {e}")
        return False

def main():
    print("="*70)
    print("FINAL CLASS CONSOLIDATION (20 → 18 classes)")
    print("="*70)
    
    dataset_path = Path("dataset")
    processed = 0
    failed = 0
    
    for folder in [dataset_path / "train" / "labels", 
                   dataset_path / "valid" / "labels",
                   dataset_path / "test" / "labels"]:
        if not folder.exists():
            print(f"⚠️  {folder} not found")
            continue
        
        files = list(folder.glob("*.txt"))
        print(f"\n📁 {folder.relative_to(dataset_path)}: {len(files)} files")
        
        for f in files:
            if consolidate_file(f):
                processed += 1
            else:
                failed += 1
    
    print(f"\n✓ Processed {processed} files (Failed: {failed})")
    
    # Verification
    print("\n" + "="*70)
    print("VERIFYING CONSOLIDATION...")
    print("="*70)
    
    from collections import Counter
    class_counts = Counter()
    
    for txt_file in dataset_path.rglob("*.txt"):
        with open(txt_file) as f:
            for line in f:
                parts = line.split()
                if parts:
                    try:
                        class_counts[int(parts[0])] += 1
                    except:
                        pass
    
    print(f"\nFinal class distribution:")
    for cls_id in sorted(class_counts.keys()):
        print(f"  Class {cls_id:2d}: {class_counts[cls_id]:4d} labels")
    
    total_unique = len(class_counts)
    total_labels = sum(class_counts.values())
    
    print(f"\nSummary:")
    print(f"  Unique classes: {total_unique} (should be 18)")
    print(f"  Total labels: {total_labels}")
    
    if total_unique == 18 and 6 not in class_counts and 9 not in class_counts:
        print("\n✅ CONSOLIDATION SUCCESSFUL!")
        print("   - Classes 6 and 9 removed")
        print("   - Reduced to 18 classes")
        print("   - Ready for retraining")
    else:
        print(f"\n❌ Consolidation incomplete:")
        print(f"   - Classes remaining: {total_unique} (expected 18)")
        print(f"   - Class 6 present: {6 in class_counts}")
        print(f"   - Class 9 present: {9 in class_counts}")

if __name__ == "__main__":
    main()
