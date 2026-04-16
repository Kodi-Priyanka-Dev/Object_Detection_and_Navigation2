"""
YOLOv8n Implementation Scripts
Multiple ready-to-use examples for different scenarios

COCO Dataset: 80 total classes
This script focuses on:
  - Humans (PRIORITY)
  - Accessories
  - Electronics
  - Furniture
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict


# ============================================================================
# CLASS CONFIGURATION
# ============================================================================

# === PRIORITY CLASS ===
HUMAN_CLASSES = [
    'person'                            # 1 class
]

# === ACCESSORIES (from COCO) ===
ACCESSORY_CLASSES = [
    'handbag',                          # bag / purse
    'tie',                              # necktie
    'suitcase',                         # luggage
    'umbrella',                         # umbrella
    'backpack',                         # backpack
]

# === ELECTRONICS (from COCO) ===
ELECTRONICS_CLASSES = [
    'tv',                               # television / monitor
    'laptop',                           # laptop computer
    'mouse',                            # computer mouse
    'remote',                           # remote control
    'keyboard',                         # computer keyboard
    'cell phone',                       # mobile phone
]

# === FURNITURE (from COCO) ===
FURNITURE_CLASSES = [
    'chair',                            # chair
    'couch',                            # sofa / couch
    'bed',                              # bed
    'dining table',                     # table
]

# All target classes combined (humans first for priority)
TARGET_CLASSES = (
    HUMAN_CLASSES +
    ACCESSORY_CLASSES +
    ELECTRONICS_CLASSES +
    FURNITURE_CLASSES
)

# Total: 1 + 5 + 6 + 4 = 16 classes out of 80 COCO classes

# Color map per category (BGR format for OpenCV)
CATEGORY_COLORS = {
    'human':       (0, 0, 255),         # Red   — highest priority
    'accessory':   (0, 215, 255),       # Gold
    'electronics': (255, 180, 0),       # Blue-orange
    'furniture':   (0, 200, 100),       # Green
}

def get_class_color(cls_name):
    """Return BGR color based on class category."""
    if cls_name in HUMAN_CLASSES:
        return CATEGORY_COLORS['human']
    elif cls_name in ACCESSORY_CLASSES:
        return CATEGORY_COLORS['accessory']
    elif cls_name in ELECTRONICS_CLASSES:
        return CATEGORY_COLORS['electronics']
    elif cls_name in FURNITURE_CLASSES:
        return CATEGORY_COLORS['furniture']
    return (200, 200, 200)             # Gray fallback


def get_class_category(cls_name):
    """Return category label for a class name."""
    if cls_name in HUMAN_CLASSES:
        return 'HUMAN ★'
    elif cls_name in ACCESSORY_CLASSES:
        return 'Accessory'
    elif cls_name in ELECTRONICS_CLASSES:
        return 'Electronics'
    elif cls_name in FURNITURE_CLASSES:
        return 'Furniture'
    return 'Other'


def get_display_label(cls_name):
    """Normalize class label for user-facing output/UI text."""
    if cls_name == 'dining table':
        return 'Table'
    return cls_name


# ============================================================================
# SCRIPT 1: Basic Image Detection (with class filter)
# ============================================================================

def detect_objects_in_image(image_path, output_path='result.jpg', conf=0.5):
    """
    Detect objects in a single image — filtered to target classes only.

    Args:
        image_path: Path to input image
        output_path: Path to save annotated image
        conf: Confidence threshold (0-1)
    """
    print("Loading model...")
    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Attempting to download YOLOv8n...")
        try:
            model = YOLO('yolov8n.pt')  # Auto-downloads
            print("✅ Downloaded successfully!")
        except Exception as e2:
            print(f"❌ Download failed: {e2}")
            return

    print(f"Processing image: {image_path}")
    results = model.predict(source=image_path, conf=conf)

    image = cv2.imread(image_path)

    humans_found = []
    others_found = []

    for result in results:
        for box in result.boxes:
            cls_name = result.names[int(box.cls[0])]

            if cls_name not in TARGET_CLASSES:
                continue

            confidence = box.conf[0].item()
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = get_class_color(cls_name)
            category = get_class_category(cls_name)
            display_name = get_display_label(cls_name)
            label = f"{display_name} ({confidence:.2f})"

            # Draw bounding box (thicker for humans)
            thickness = 3 if cls_name in HUMAN_CLASSES else 2
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

            # Label background
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(image, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(image, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            entry = {
                'class': display_name,
                'category': category,
                'confidence': confidence,
                'bbox': (x1, y1, x2, y2)
            }

            if cls_name in HUMAN_CLASSES:
                humans_found.append(entry)
            else:
                others_found.append(entry)

    # Print humans first
    print(f"\n{'='*50}")
    print(f"  HUMANS (priority): {len(humans_found)} detected")
    print(f"{'='*50}")
    for h in humans_found:
        print(f"  ★ person  | conf: {h['confidence']:.3f} | box: {h['bbox']}")

    print(f"\n  OTHER TARGET CLASSES: {len(others_found)} detected")
    print(f"{'-'*50}")
    for o in others_found:
        print(f"  [{o['category']:12}] {o['class']:15} | conf: {o['confidence']:.3f}")

    cv2.imwrite(output_path, image)
    print(f"\nAnnotated image saved to: {output_path}")


# ============================================================================
# SCRIPT 2: Real-time Webcam Detection
# ============================================================================

def webcam_detection(conf=0.5, fps_limit=30):
    """
    Real-time object detection using webcam — filtered classes only.

    Controls:
        'q' - Quit
        's' - Save screenshot
    """
    print("Loading model...")
    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Attempting to download YOLOv8n...")
        try:
            model = YOLO('yolov8n.pt')  # Auto-downloads
            print("✅ Downloaded successfully!")
        except Exception as e2:
            print(f"❌ Download failed: {e2}")
            return

    print("Starting webcam detection (press 'q' to quit)...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % max(1, (30 // fps_limit)) != 0:
            continue

        results = model(frame, conf=conf)
        annotated = frame.copy()

        person_count = 0

        for result in results:
            for box in result.boxes:
                cls_name = result.names[int(box.cls[0])]
                if cls_name not in TARGET_CLASSES:
                    continue

                confidence = box.conf[0].item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = get_class_color(cls_name)
                label = f"{cls_name} {confidence:.2f}"
                thickness = 3 if cls_name in HUMAN_CLASSES else 2

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(annotated, label, (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                if cls_name == 'person':
                    person_count += 1

        # HUD overlay
        cv2.putText(annotated, f"Frame: {frame_count}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(annotated, f"Humans: {person_count}", (10, 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow('YOLOv8n — Human + Accessories + Electronics + Furniture', annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            fname = f'screenshot_{frame_count}.jpg'
            cv2.imwrite(fname, annotated)
            print(f"Screenshot saved: {fname}")

    cap.release()
    cv2.destroyAllWindows()
    print("Webcam detection stopped.")


# ============================================================================
# SCRIPT 3: Video File Processing
# ============================================================================

def process_video(input_video, output_video='output.mp4', conf=0.5):
    """
    Process video file and save with filtered detections.

    Args:
        input_video: Path to input video
        output_video: Path to save output video
        conf: Confidence threshold
    """
    print("Loading model...")
    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Attempting to download YOLOv8n...")
        try:
            model = YOLO('yolov8n.pt')  # Auto-downloads
            print("✅ Downloaded successfully!")
        except Exception as e2:
            print(f"❌ Download failed: {e2}")
            return

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print(f"Error: Could not open video {input_video}")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {width}x{height} @ {fps}fps — {total_frames} frames")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, conf=conf)
            annotated = frame.copy()

            for result in results:
                for box in result.boxes:
                    cls_name = result.names[int(box.cls[0])]
                    if cls_name not in TARGET_CLASSES:
                        continue

                    confidence = box.conf[0].item()
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = get_class_color(cls_name)
                    label = f"{cls_name} {confidence:.2f}"
                    thickness = 3 if cls_name in HUMAN_CLASSES else 2

                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                    cv2.putText(annotated, label, (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            out.write(annotated)
            frame_count += 1

            if frame_count % 30 == 0:
                pct = (frame_count / total_frames) * 100
                print(f"Progress: {frame_count}/{total_frames} ({pct:.1f}%)")

    finally:
        cap.release()
        out.release()
        print(f"\nDone! Output saved to: {output_video}")


# ============================================================================
# SCRIPT 4: Object Counting & Statistics
# ============================================================================

class ObjectAnalyzer:
    """Analyze and count target-class objects; humans reported first."""

    def __init__(self, model_path='yolov8n.pt'):
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("   Attempting to download YOLOv8n...")
            try:
                self.model = YOLO('yolov8n.pt')  # Auto-downloads
                print("✅ Downloaded successfully!")
            except Exception as e2:
                print(f"❌ Download failed: {e2}")
                self.model = None
        
        self.class_counts = defaultdict(int)
        self.confidence_scores = defaultdict(list)

    def analyze_image(self, image_path, conf=0.5):
        if self.model is None:
            print("❌ Model not available")
            return {}
        
        results = self.model.predict(source=image_path, conf=conf)
        stats = {}

        for result in results:
            for box in result.boxes:
                cls_name = result.names[int(box.cls[0])]
                if cls_name not in TARGET_CLASSES:
                    continue

                confidence = box.conf[0].item()
                self.class_counts[cls_name] += 1
                self.confidence_scores[cls_name].append(confidence)

                stats[cls_name] = {
                    'category': get_class_category(cls_name),
                    'count': self.class_counts[cls_name],
                    'avg_confidence': np.mean(self.confidence_scores[cls_name])
                }

        return stats

    def analyze_video(self, video_path, conf=0.5, interval=5):
        if self.model is None:
            print("❌ Model not available")
            return
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % (fps * interval) == 0:
                results = self.model(frame, conf=conf)
                for result in results:
                    for box in result.boxes:
                        cls_name = result.names[int(box.cls[0])]
                        if cls_name not in TARGET_CLASSES:
                            continue
                        confidence = box.conf[0].item()
                        self.class_counts[cls_name] += 1
                        self.confidence_scores[cls_name].append(confidence)

                print(f"Analyzed frame {frame_count}/{total_frames}")

            frame_count += 1

        cap.release()
        self.print_statistics()

    def print_statistics(self):
        print("\n" + "="*55)
        print("  DETECTION STATISTICS")
        print("="*55)

        # Humans first
        print("\n  [HUMANS — PRIORITY]")
        for cls in HUMAN_CLASSES:
            if cls in self.class_counts:
                count = self.class_counts[cls]
                avg = np.mean(self.confidence_scores[cls])
                print(f"  ★ {cls:15} Count: {count:4}  Avg Conf: {avg:.3f}")

        # Other categories
        for category, classes in [
            ('ACCESSORIES',  ACCESSORY_CLASSES),
            ('ELECTRONICS',  ELECTRONICS_CLASSES),
            ('FURNITURE',    FURNITURE_CLASSES),
        ]:
            found = [c for c in classes if c in self.class_counts]
            if found:
                print(f"\n  [{category}]")
                for cls in found:
                    count = self.class_counts[cls]
                    avg = np.mean(self.confidence_scores[cls])
                    print(f"    {get_display_label(cls):18} Count: {count:4}  Avg Conf: {avg:.3f}")

        print("\n" + "-"*55)
        print(f"  Total detections: {sum(self.class_counts.values())}")

    def get_statistics(self):
        return {
            'total_detections': sum(self.class_counts.values()),
            'class_counts': dict(self.class_counts),
            'avg_confidence': {
                cls: np.mean(scores)
                for cls, scores in self.confidence_scores.items()
            }
        }


# ============================================================================
# SCRIPT 5: Object Detection with Filtering
# ============================================================================

def detect_specific_objects(image_path, target_classes=None, conf=0.5):
    """
    Detect only specific object classes.
    Defaults to TARGET_CLASSES (humans + accessories + electronics + furniture).

    Args:
        image_path: Path to image
        target_classes: Override list of class names (None = use TARGET_CLASSES)
        conf: Confidence threshold
    """
    print("Loading model...")
    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Attempting to download YOLOv8n...")
        try:
            model = YOLO('yolov8n.pt')  # Auto-downloads
            print("✅ Downloaded successfully!")
        except Exception as e2:
            print(f"❌ Download failed: {e2}")
            return
    
    results = model.predict(source=image_path, conf=conf)

    if target_classes is None:
        target_classes = TARGET_CLASSES

    print(f"Filtering for {len(target_classes)} classes:")
    print(f"  Humans      : {HUMAN_CLASSES}")
    print(f"  Accessories : {ACCESSORY_CLASSES}")
    print(f"  Electronics : {ELECTRONICS_CLASSES}")
    print(f"  Furniture   : {FURNITURE_CLASSES}")

    for result in results:
        detections = {cls: [] for cls in target_classes}

        for box in result.boxes:
            cls_name = result.names[int(box.cls[0])]
            if cls_name not in target_classes:
                continue

            x1, y1, x2, y2 = box.xyxy[0]
            confidence = box.conf[0].item()
            detections[cls_name].append({
                'confidence': confidence,
                'bbox': (int(x1), int(y1), int(x2), int(y2))
            })

        # Print humans first, then rest
        print(f"\n{'='*50}")
        print("  HUMANS (priority):")
        for cls in HUMAN_CLASSES:
            dets = detections.get(cls, [])
            if dets:
                print(f"  ★ {cls}: {len(dets)} detected")
                for i, d in enumerate(dets):
                    print(f"      [{i+1}] conf: {d['confidence']:.3f}  box: {d['bbox']}")

        for group_name, group_classes in [
            ('ACCESSORIES',  ACCESSORY_CLASSES),
            ('ELECTRONICS',  ELECTRONICS_CLASSES),
            ('FURNITURE',    FURNITURE_CLASSES),
        ]:
            group_found = [(c, detections[c]) for c in group_classes if detections.get(c)]
            if group_found:
                print(f"\n  {group_name}:")
                for cls_name, dets in group_found:
                    print(f"    {cls_name}: {len(dets)} detected")
                    for i, d in enumerate(dets):
                        print(f"      [{i+1}] conf: {d['confidence']:.3f}  box: {d['bbox']}")


# ============================================================================
# MAIN - Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("YOLOv8n — Class Summary")
    print("="*50)
    print(f"  Total COCO classes     : 80")
    print(f"  Classes used here      : {len(TARGET_CLASSES)}")
    print(f"    Humans (priority)    : {len(HUMAN_CLASSES)}   → {HUMAN_CLASSES}")
    print(f"    Accessories          : {len(ACCESSORY_CLASSES)}   → {ACCESSORY_CLASSES}")
    print(f"    Electronics          : {len(ELECTRONICS_CLASSES)}  → {ELECTRONICS_CLASSES}")
    print(f"    Furniture            : {len(FURNITURE_CLASSES)}   → {FURNITURE_CLASSES}")
    print()

    # Example 1: Image detection
    # detect_objects_in_image('path/to/image.jpg')

    # Example 2: Webcam detection
    # webcam_detection(conf=0.5)

    # Example 3: Video processing
    # process_video('input.mp4', 'output.mp4')

    # Example 4: Object analysis
    # analyzer = ObjectAnalyzer()
    # analyzer.analyze_image('path/to/image.jpg')
    # analyzer.print_statistics()

    # Example 5: Filter specific objects
    # detect_specific_objects('path/to/image.jpg')

    print("Uncomment the desired example and replace file paths to run!")
