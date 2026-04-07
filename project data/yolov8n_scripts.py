"""
YOLOv8n Implementation Scripts
Multiple ready-to-use examples for different scenarios
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict


# ============================================================================
# SCRIPT 1: Basic Image Detection
# ============================================================================

def detect_objects_in_image(image_path, output_path='result.jpg', conf=0.5):
    """
    Detect objects in a single image
    
    Args:
        image_path: Path to input image
        output_path: Path to save annotated image
        conf: Confidence threshold (0-1)
    """
    print(f"Loading model...")
    model = YOLO('yolov8n.pt')
    
    print(f"Processing image: {image_path}")
    results = model.predict(source=image_path, conf=conf)
    
    for result in results:
        print(f"\nDetected objects:")
        for box in result.boxes:
            cls_name = result.names[int(box.cls[0])]
            confidence = box.conf[0].item()
            print(f"  - {cls_name}: {confidence:.2f}")
        
        # Save annotated image
        result.save(filename=output_path)
        print(f"Saved to: {output_path}")


# ============================================================================
# SCRIPT 2: Real-time Webcam Detection
# ============================================================================

def webcam_detection(conf=0.5, fps_limit=30):
    """
    Real-time object detection using webcam
    
    Args:
        conf: Confidence threshold
        fps_limit: Limit FPS for performance
    
    Controls:
        'q' - Quit
        's' - Save screenshot
    """
    print("Loading model...")
    model = YOLO('yolov8n.pt')
    
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
        
        # Skip frames to control FPS
        if frame_count % (30 // fps_limit) != 0:
            continue
        
        # Run inference
        results = model(frame, conf=conf)
        annotated_frame = results[0].plot()
        
        # Add FPS counter
        cv2.putText(annotated_frame, f"Frame: {frame_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display
        cv2.imshow('YOLOv8n Webcam Detection', annotated_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'screenshot_{frame_count}.jpg', annotated_frame)
            print(f"Screenshot saved: screenshot_{frame_count}.jpg")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Webcam detection stopped")


# ============================================================================
# SCRIPT 3: Video File Processing
# ============================================================================

def process_video(input_video, output_video='output.mp4', conf=0.5):
    """
    Process video file and save with detections
    
    Args:
        input_video: Path to input video
        output_video: Path to save output video
        conf: Confidence threshold
    """
    print(f"Loading model...")
    model = YOLO('yolov8n.pt')
    
    print(f"Opening video: {input_video}")
    cap = cv2.VideoCapture(input_video)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {input_video}")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height}, {fps}fps, {total_frames} frames")
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run inference
            results = model(frame, conf=conf)
            annotated_frame = results[0].plot()
            
            # Write frame
            out.write(annotated_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {frame_count}/{total_frames} ({progress:.1f}%)")
    
    finally:
        cap.release()
        out.release()
        print(f"\nVideo processing complete!")
        print(f"Output saved to: {output_video}")


# ============================================================================
# SCRIPT 4: Object Counting & Statistics
# ============================================================================

class ObjectAnalyzer:
    """Analyze and count objects in video"""
    
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        self.class_counts = defaultdict(int)
        self.confidence_scores = defaultdict(list)
    
    def analyze_image(self, image_path, conf=0.5):
        """Analyze single image"""
        results = self.model.predict(source=image_path, conf=conf)
        
        stats = {}
        for result in results:
            for box in result.boxes:
                cls_name = result.names[int(box.cls[0])]
                confidence = box.conf[0].item()
                
                self.class_counts[cls_name] += 1
                self.confidence_scores[cls_name].append(confidence)
                
                stats[cls_name] = {
                    'count': self.class_counts[cls_name],
                    'avg_confidence': np.mean(self.confidence_scores[cls_name])
                }
        
        return stats
    
    def analyze_video(self, video_path, conf=0.5, interval=5):
        """Analyze video at specific intervals"""
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        analyzed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze every nth frame
            if frame_count % (fps * interval) == 0:
                results = self.model(frame, conf=conf)
                for result in results:
                    for box in result.boxes:
                        cls_name = result.names[int(box.cls[0])]
                        confidence = box.conf[0].item()
                        self.class_counts[cls_name] += 1
                        self.confidence_scores[cls_name].append(confidence)
                
                analyzed_frames += 1
                print(f"Analyzed frame {frame_count}/{total_frames}")
            
            frame_count += 1
        
        cap.release()
        
        # Print statistics
        print("\n=== Detection Statistics ===")
        for cls_name in sorted(self.class_counts.keys()):
            count = self.class_counts[cls_name]
            avg_conf = np.mean(self.confidence_scores[cls_name])
            print(f"{cls_name:15} - Count: {count:4}, Avg Confidence: {avg_conf:.3f}")
    
    def get_statistics(self):
        """Get summary statistics"""
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
    Detect only specific object classes
    
    Args:
        image_path: Path to image
        target_classes: List of class names to detect (None = all)
                       Example: ['person', 'car', 'dog']
        conf: Confidence threshold
    """
    model = YOLO('yolov8n.pt')
    results = model.predict(source=image_path, conf=conf)
    
    print(f"All available classes in YOLOv8n:")
    print(list(results[0].names.values()))
    
    if target_classes is None:
        target_classes = list(results[0].names.values())
    
    print(f"\nFiltering for: {target_classes}")
    
    for result in results:
        detections = {cls: [] for cls in target_classes}
        
        for box in result.boxes:
            cls_name = result.names[int(box.cls[0])]
            
            if cls_name in target_classes:
                x1, y1, x2, y2 = box.xyxy[0]
                confidence = box.conf[0].item()
                
                detections[cls_name].append({
                    'confidence': confidence,
                    'bbox': (int(x1), int(y1), int(x2), int(y2))
                })
        
        # Print results
        for cls_name, dets in detections.items():
            if dets:
                print(f"{cls_name}: {len(dets)} detected")
                for i, det in enumerate(dets):
                    print(f"  [{i+1}] Confidence: {det['confidence']:.3f}, "
                          f"Box: {det['bbox']}")


# ============================================================================
# MAIN - Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Image detection
    print("Example 1: Image Detection")
    print("-" * 50)
    # detect_objects_in_image('path/to/image.jpg')
    
    # Example 2: Webcam detection
    print("\nExample 2: Webcam Detection")
    print("-" * 50)
    # webcam_detection(conf=0.5)
    
    # Example 3: Video processing
    print("\nExample 3: Video Processing")
    print("-" * 50)
    # process_video('input.mp4', 'output.mp4')
    
    # Example 4: Object analysis
    print("\nExample 4: Object Analysis")
    print("-" * 50)
    analyzer = ObjectAnalyzer()
    # analyzer.analyze_image('path/to/image.jpg')
    # print(analyzer.get_statistics())
    
    # Example 5: Filter specific objects
    print("\nExample 5: Filter Specific Objects")
    print("-" * 50)
    # detect_specific_objects('path/to/image.jpg', 
    #                        target_classes=['person', 'car'])
    
    print("\nUncomment the desired example to run it!")
    print("Make sure to replace file paths with actual paths to your files.")
