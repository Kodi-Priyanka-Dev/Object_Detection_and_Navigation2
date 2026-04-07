"""Debug consolidation to see what's happening"""
from pathlib import Path

# Check a single file to debug
test_file = next(Path("dataset/train/labels").glob("*.txt"))
print(f"Testing file: {test_file.name}")

# Check current content
with open(test_file) as f:
    content = f.read()
    lines = content.split('\n')
    print(f"\nFile has {len([l for l in lines if l.strip()])} labels")
    print("First 3 lines:")
    for i, line in enumerate(lines[:3]):
        if line.strip():
            parts = line.split()
            print(f"  Line {i}: class={parts[0]} (type: {type(parts[0])})")

# Manual test of remapping
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

# Test remapping
print("\nTesting remapping:")
for old_cls in [5, 6, 8, 9]:
    new_cls = CLASS_REMAPPING.get(old_cls, old_cls)
    print(f"  {old_cls} → {new_cls}")

# Check what's in the file
print("\nUnique classes in test file:")
with open(test_file) as f:
    classes = set()
    for line in f:
        parts = line.split()
        if parts:
            try:
                classes.add(int(parts[0]))
            except:
                pass
print(sorted(classes))
