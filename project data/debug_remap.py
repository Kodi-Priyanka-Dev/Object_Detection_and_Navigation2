"""Debug remapping for classes 6 and 9"""
from pathlib import Path

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

# Find files with class 6 or 9
files_with_6 = []
files_with_9 = []

for txt_file in Path('dataset').rglob('*.txt'):
    with open(txt_file) as f:
        content = f.read()
        for line in content.split('\n'):
            parts = line.strip().split()
            if parts and len(parts) > 0:
                try:
                    cls_id = int(parts[0])
                    if cls_id == 6 and not files_with_6:
                        files_with_6.append(txt_file)
                    if cls_id == 9 and not files_with_9:
                        files_with_9.append(txt_file)
                except:
                    pass

# Test the remapping on one file with class 6
if files_with_6:
    test_file = files_with_6[0]
    print(f"Testing file with class 6: {test_file.name}")
    
    with open(test_file) as f:
        lines = f.readlines()
    
    print(f"Original file ({len(lines)} lines):")
    for line in lines[:5]:
        parts = line.split()
        if parts:
            print(f"  Class {parts[0]}: {line.strip()}")
    
    # Manual remapping
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) > 0:
            try:
                old_cls = int(parts[0])
                new_cls = CLASS_REMAPPING.get(old_cls, old_cls)
                print(f"Mapping: {old_cls} → {new_cls}")
                break  # Just show first one
            except:
                pass
