"""
Comprehensive class consolidation with detailed logging
"""
import os
from pathlib import Path

# Define class remapping
CLASS_REMAPPING = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
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

def consolidate_file(filepath):
    """Process and return statistics"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        classes_before = set()
        classes_after = set()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) > 0:
                try:
                    old_cls = int(parts[0])
                    classes_before.add(old_cls)
                    new_cls = CLASS_REMAPPING.get(old_cls, old_cls)
                    classes_after.add(new_cls)
                    new_line = f"{new_cls} " + " ".join(parts[1:]) + "\n"
                    new_lines.append(new_line)
                except (ValueError, IndexError):
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Write back
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        
        return True, classes_before, classes_after
    except Exception as e:
        print(f"ERROR processing {filepath}: {e}")
        return False, set(), set()

def main():
    dataset_path = Path("dataset")
    
    # Statistics
    total_files = 0
    processed_files = 0
    failed_files = 0
    all_classes_before = set()
    all_classes_after = set()
    
    target_folders = [
        dataset_path / "train" / "labels",
        dataset_path / "valid" / "labels",
        dataset_path / "test" / "labels",
    ]
    
    print("=" * 70)
    print("COMPREHENSIVE CLASS CONSOLIDATION")
    print("=" * 70)
    
    for folder in target_folders:
        if not folder.exists():
            print(f"⚠️  Folder does not exist: {folder}")
            continue
        
        print(f"\n📁 Processing: {folder.parent.name}/{folder.name}/")
        files = list(folder.glob("*.txt"))
        print(f"   Found {len(files)} label files")
        
        for label_file in files:
            total_files += 1
            success, before, after = consolidate_file(label_file)
            if success:
                processed_files += 1
                all_classes_before.update(before)
                all_classes_after.update(after)
            else:
                failed_files += 1
    
    print("\n" + "=" * 70)
    print("CONSOLIDATION RESULTS")
    print("=" * 70)
    print(f"Total files processed: {processed_files}/{total_files}")
    print(f"Failed files: {failed_files}")
    print(f"\nClasses found BEFORE: {sorted(all_classes_before)}")
    print(f"Classes found AFTER: {sorted(all_classes_after)}")
    
    # Verification
    if 6 in all_classes_after or 9 in all_classes_after:
        print("\n❌ CONSOLIDATION INCOMPLETE - Old classes still present!")
        print(f"   Class 6 remaining: {6 in all_classes_after}")
        print(f"   Class 9 remaining: {9 in all_classes_after}")
    else:
        print("\n✅ CONSOLIDATION SUCCESSFUL - All old classes removed!")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
