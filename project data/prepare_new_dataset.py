#!/usr/bin/env python3
"""
Prepare New Dataset for Fine-Tuning
===================================

Converts XML annotations (Roboflow format) to YOLO format
and creates proper directory structure for training.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

# Class mapping (must match the consolidated classes)
CLASS_NAMES = {
    0: 'Digital Board',
    1: 'Door',
    2: 'Glass Door',
    3: 'Machine',
    4: 'Table',
    5: 'chair',
    6: 'flowervase',
    7: 'round chair',
    8: 'human',
    9: 'sofa',
    10: 'stand',
    11: 'wall',
    12: 'wall corner',
    13: 'wall edge',
    14: 'water filter',
    15: 'window',
    16: 'wooden entrance',
    17: 'wooden stand'
}

# Reverse mapping: class name -> class id
CLASS_TO_ID = {v: k for k, v in CLASS_NAMES.items()}

def xml_to_yolo(xml_file, image_width, image_height):
    """Convert XML bounding boxes to YOLO format"""
    yolo_annotations = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        for obj in root.findall('object'):
            class_name = obj.find('name').text
            
            # Skip if class not in our mapping
            if class_name not in CLASS_TO_ID:
                print(f"⚠️  Warning: Unknown class '{class_name}' in {xml_file}")
                continue
            
            class_id = CLASS_TO_ID[class_name]
            
            # Get bounding box
            bndbox = obj.find('bndbox')
            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)
            
            # Convert to YOLO format (center x, center y, width, height) normalized
            center_x = (xmin + xmax) / 2.0 / image_width
            center_y = (ymin + ymax) / 2.0 / image_height
            width = (xmax - xmin) / image_width
            height = (ymax - ymin) / image_height
            
            # Clamp values to [0, 1]
            center_x = max(0, min(1, center_x))
            center_y = max(0, min(1, center_y))
            width = max(0, min(1, width))
            height = max(0, min(1, height))
            
            yolo_annotations.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
        
        return yolo_annotations
    except Exception as e:
        print(f"❌ Error converting {xml_file}: {e}")
        return []

def get_image_dimensions(xml_file):
    """Get image width and height from XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        width = int(root.find('size/width').text)
        height = int(root.find('size/height').text)
        return width, height
    except:
        return 640, 640  # Default size

def process_dataset():
    """Process the new dataset"""
    base_path = r"C:\Users\Priyanka\Documents\project data\New dataset\SyntheticIndoorObjectDetectionDataset"
    output_path = r"C:\Users\Priyanka\Documents\project data\dataset_fine_tune"
    
    print("\n" + "=" * 80)
    print("🔄 PREPARING NEW DATASET FOR FINE-TUNING")
    print("=" * 80)
    
    # Create output directory structure
    for split in ['train', 'val', 'test']:
        os.makedirs(f"{output_path}/{split}/images", exist_ok=True)
        os.makedirs(f"{output_path}/{split}/labels", exist_ok=True)
    
    total_annotations = 0
    total_skipped = 0
    
    # Process each split
    for split in ['train', 'valid', 'test']:  # Note: Roboflow uses 'valid' not 'val'
        input_dir = f"{base_path}/{split}"
        output_split = 'val' if split == 'valid' else split
        output_dir = f"{output_path}/{output_split}"
        
        if not os.path.exists(input_dir):
            print(f"⚠️  {split} directory not found: {input_dir}")
            continue
        
        print(f"\n📂 Processing {split.upper()} set...")
        
        # Find all XML files
        xml_files = sorted(Path(input_dir).glob("*.xml"))
        print(f"   Found {len(xml_files)} annotations")
        
        for i, xml_file in enumerate(xml_files):
            if (i + 1) % max(1, len(xml_files) // 10) == 0:
                print(f"   Progress: {i+1}/{len(xml_files)}")
            # Get corresponding image
            base_name = xml_file.stem
            img_file = None
            for ext in ['.jpg', '.jpeg', '.png']:
                candidate = f"{input_dir}/{base_name}{ext}"
                if os.path.exists(candidate):
                    img_file = candidate
                    break
            
            if not img_file:
                total_skipped += 1
                continue
            
            # Get image dimensions
            width, height = get_image_dimensions(str(xml_file))
            
            # Convert XML to YOLO
            yolo_annotations = xml_to_yolo(str(xml_file), width, height)
            
            if not yolo_annotations:
                total_skipped += 1
                continue
            
            # Copy image
            dst_img = f"{output_dir}/images/{base_name}.jpg"
            shutil.copy2(img_file, dst_img)
            
            # Write YOLO labels
            dst_label = f"{output_dir}/labels/{base_name}.txt"
            with open(dst_label, 'w') as f:
                f.write('\n'.join(yolo_annotations))
            
            total_annotations += len(yolo_annotations)
        
        print(f"   ✅ Processed: {len(xml_files)} images")
    
    # Create data.yaml
    yaml_content = """path: """ + output_path.replace("\\", "/") + """
train: train/images
val: val/images
test: test/images

nc: 18
names:
  0: Digital Board
  1: Door
  2: Glass Door
  3: Machine
  4: Table
  5: chair
  6: flowervase
  7: round chair
  8: human
  9: sofa
  10: stand
  11: wall
  12: wall corner
  13: wall edge
  14: water filter
  15: window
  16: wooden entrance
  17: wooden stand
"""
    
    with open(f"{output_path}/data.yaml", 'w') as f:
        f.write(yaml_content)
    
    # Count images and labels
    train_imgs = len(list(Path(f"{output_path}/train/images").glob("*")))
    val_imgs = len(list(Path(f"{output_path}/val/images").glob("*")))
    test_imgs = len(list(Path(f"{output_path}/test/images").glob("*")))
    
    print("\n" + "=" * 80)
    print("✅ DATASET PREPARATION COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Training images:   {train_imgs}")
    print(f"   Validation images: {val_imgs}")
    print(f"   Test images:       {test_imgs}")
    print(f"   Total annotations: {total_annotations}")
    print(f"   Skipped:           {total_skipped}")
    print(f"\n📁 Output path: {output_path}")
    print(f"📝 Config file: {output_path}/data.yaml")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    process_dataset()
