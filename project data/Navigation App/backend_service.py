"""
Flask Backend Service for YOLO Object Detection
================================================
Provides REST API for Flutter app to send frames and receive detection results
"""

# Enable CUDA for GPU acceleration (if available)
import os
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Uncomment to disable CUDA

try:
    from flask import Flask, request, jsonify, Response
    from flask_cors import CORS
except ImportError as e:
    print(f"❌ Flask import error: {e}")
    print("    Run: pip install flask flask-cors")
    exit(1)

import cv2
import numpy as np
import base64
import sys
import time
import logging

# Configure logging for real-time display
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
sys.stdout.flush()
sys.stderr.flush()

try:
    import torch
    from ultralytics import YOLO
except Exception as e:
    print(f"❌ PyTorch import error: {e}")
    exit(1)

INFERENCE_DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

app = Flask(__name__)
CORS(app)

# Model confidence prefilter:
# Keep this at/below the lowest per-class threshold you intend to apply later.
MODEL_CONF_PREFILTER = float(os.getenv("MODEL_CONF_PREFILTER", "0.01"))

# Expensive diagnostic pass (extra YOLO inference) - enable only when debugging.
ENABLE_RAW_DIAGNOSTIC = os.getenv("ENABLE_RAW_DIAGNOSTIC", "0").strip().lower() in {"1", "true", "yes", "on"}

# ─── SELECT MODEL TYPE (nano for speed and accuracy) ───
MODEL_TYPE = os.getenv("MODEL_TYPE", "nano").lower()  # Using YOLOv8n (nano)

# Model paths for different variants
MODEL_PATHS = {
    "nano": os.path.join("..", "best_model", "best.pt"),      # YOLOv8n: ~6MB, 5-10ms inference
}

CUSTOM_MODEL_PATH = MODEL_PATHS.get(MODEL_TYPE, MODEL_PATHS["nano"])
MODEL_VARIANT = MODEL_TYPE.upper()

print(f"[4/4] Loading YOLOv8{MODEL_VARIANT} model...")
print(f"      🎯 Using YOLOv8{MODEL_VARIANT} fine-tuned model for all detections")
print(f"      📌 Variant: {MODEL_TYPE} (set via MODEL_TYPE environment variable)")

# Custom model (20 classes: Door, Human, Chair, etc)
custom_model = None
print(f"  📦 YOLOv8{MODEL_VARIANT} Model: {CUSTOM_MODEL_PATH} (exists: {os.path.exists(CUSTOM_MODEL_PATH)})")
try:
    custom_model = YOLO(CUSTOM_MODEL_PATH)
    if INFERENCE_DEVICE.startswith('cuda'):
        custom_model.to(INFERENCE_DEVICE)
    print(f"      ✅ YOLOv8{MODEL_VARIANT} model loaded ({len(custom_model.names)} classes)")
except Exception as e:
    print(f"      ❌ YOLOv8{MODEL_VARIANT} model error: {e}")

model = custom_model  # Keep backward compat for visualization stream

print("=" * 60)
if custom_model:
    print(f"✅ BACKEND READY - YOLOv8{MODEL_VARIANT} model loaded on port 5000")
else:
    print(f"❌ WARNING - YOLOv8{MODEL_VARIANT} model failed to load!")
print("=" * 60)

# ─── VERIFY CUSTOM MODEL CLASS NAMES ───
print("\n📋 CUSTOM MODEL CLASS NAMES (for verification):")
if custom_model:
    for idx, cls_name in custom_model.names.items():
        print(f"   Class {idx}: '{cls_name}'")
else:
    print("   ❌ Custom model not loaded")
print("=" * 60 + "\n")

# ─── CLASS CONSOLIDATION MAPPING ───
# Consolidates duplicates and plurals to singular forms
CLASS_CONSOLIDATION_MAP = {
    "chairs": "chair",           # Plural to singular
    "humans": "human",           # Plural to singular
    "round chair": "chair",      # Consolidate variants to single "chair"
    "glass door": "door",        # Consolidate door variants
    "wooden entrance": "door",   # Consolidate to door
    # Keep singular forms as-is by not mapping them
}

def consolidate_class_name(cls_name):
    """Convert class name to consolidated singular form"""
    cls_lower = cls_name.lower().strip()
    return CLASS_CONSOLIDATION_MAP.get(cls_lower, cls_name)

print("🔄 CLASS CONSOLIDATION MAP:")
print("   'chairs' -> 'chair'")
print("   'humans' -> 'human'")
print("   'round chair' -> 'chair'")
print("   'glass door' -> 'door'")
print("   'wooden entrance' -> 'door'")
print("=" * 60 + "\n")

# Distance estimation per class
OBJECT_WIDTHS = {
    "door": 0.9, "glass door": 0.9, "wooden entrance": 0.9,
    "human": 0.5,  # Covers all person/human variants (consolidated)
    "chair": 0.5, "round chair": 0.5,  # Consolidated: "chairs" merged into "chair"
    "sofa": 1.5, "couch": 1.5, "table": 1.2,
    "backpack": 0.35, "handbag": 0.3, "suitcase": 0.5, "bottle": 0.08,
}
FOCAL_LENGTH = 800

def estimate_distance(pixel_width, class_name=""):
    """Estimate distance to object based on pixel width and class"""
    if pixel_width == 0:
        return 0
    known_w = OBJECT_WIDTHS.get(class_name.lower(), 0.5)
    return round((known_w * FOCAL_LENGTH) / pixel_width, 2)

# ─── EDGE DETECTION FUNCTIONS ───
def detect_edges_sobel(frame, kernel_size=3):
    """
    Detect edges using Sobel operator (Sobel X, Sobel Y, combined)
    Returns edge map, edge statistics, and structural features
    """
    if frame is None or frame.size == 0:
        return None, None
    
    # Convert to grayscale if needed
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
    
    # Sobel edge detection in X direction
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=kernel_size)
    
    # Sobel edge detection in Y direction
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=kernel_size)
    
    # Compute edge magnitude
    magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
    
    # Compute edge direction (angle)
    direction = np.arctan2(sobel_y, sobel_x) * 180 / np.pi
    
    # Create a binary edge map (threshold the magnitude)
    edge_threshold = 50
    edges_binary = cv2.threshold(magnitude, edge_threshold, 255, cv2.THRESH_BINARY)[1]
    
    # Extract edge statistics
    edge_stats = {
        "total_edge_pixels": int(np.sum(edges_binary > 0)),
        "edge_percentage": round(np.sum(edges_binary > 0) / edges_binary.size * 100, 2),
        "max_edge_strength": int(magnitude.max()),
        "mean_edge_strength": round(magnitude.mean(), 2),
        "frame_height": frame.shape[0],
        "frame_width": frame.shape[1]
    }
    
    return {
        "magnitude": magnitude,
        "binary": edges_binary,
        "x_gradient": sobel_x.astype(np.uint8),
        "y_gradient": sobel_y.astype(np.uint8),
        "direction": direction
    }, edge_stats

def analyze_structural_features(edges_binary, edge_stats, frame_height):
    """
    Analyze structural features from edge map
    Detects walls, doorways, and room boundaries
    """
    features = {
        "walls": [],
        "horizontal_edges": 0,
        "vertical_edges": 0,
        "doorway_indicators": 0,
        "obstruction_level": "low"
    }
    
    # Count horizontal edges (potential walls/floors/ceiling)
    if edge_stats["total_edge_pixels"] > 0:
        # Analyze top, middle, bottom sections for walls
        h, w = edges_binary.shape
        
        # Top section (ceiling/upper wall)
        top_section = edges_binary[:h//4]
        features["walls"].append({
            "location": "ceiling",
            "edge_density": round(np.sum(top_section > 0) / top_section.size * 100, 2)
        })
        
        # Bottom section (floor/lower wall)
        bottom_section = edges_binary[3*h//4:]
        features["walls"].append({
            "location": "floor",
            "edge_density": round(np.sum(bottom_section > 0) / bottom_section.size * 100, 2)
        })
        
        # Left and right walls
        left_section = edges_binary[:, :w//4]
        features["walls"].append({
            "location": "left_wall",
            "edge_density": round(np.sum(left_section > 0) / left_section.size * 100, 2)
        })
        
        right_section = edges_binary[:, 3*w//4:]
        features["walls"].append({
            "location": "right_wall",
            "edge_density": round(np.sum(right_section > 0) / right_section.size * 100, 2)
        })
        
        # Detect doorway indicators (vertical edges with gaps)
        edges_with_gaps = detect_vertical_gaps(edges_binary)
        features["doorway_indicators"] = edges_with_gaps
        
        # Determine obstruction level based on edge density
        if edge_stats["edge_percentage"] > 20:
            features["obstruction_level"] = "high"
        elif edge_stats["edge_percentage"] > 10:
            features["obstruction_level"] = "medium"
        else:
            features["obstruction_level"] = "low"
    
    return features

def detect_vertical_gaps(edges_binary):
    """
    Detect vertical gaps in edges (potential doorways or openings)
    Returns count of potential doorway locations
    """
    h, w = edges_binary.shape
    vertical_gaps = 0
    
    # Focus on middle section (body height for doorways)
    middle_section = edges_binary[h//4:3*h//4, :]
    
    # Scan for vertical discontinuities
    for col in range(0, w, 50):  # Sample every 50 pixels
        col_edges = middle_section[:, col:min(col+50, w)]
        gap_size = 0
        max_gap = 0
        
        for row in range(col_edges.shape[0]):
            if col_edges[row].sum() == 0:
                gap_size += 1
            else:
                max_gap = max(max_gap, gap_size)
                gap_size = 0
        
        # If found a gap larger than threshold, it's a potential passage/doorway
        if max_gap > h // 8:
            vertical_gaps += 1
    
    return int(vertical_gaps)

# Global variables for video streaming
current_visualization_frame = None
visualization_lock = __import__('threading').Lock()

def generate_visualization_frames():
    """
    Generate visualization frames with detection overlays
    Used for real-time streaming to Flutter app debug panel
    """
    global current_visualization_frame
    
    # Open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("📹 Visualization stream started")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        try:
            frame_h, frame_w = frame.shape[:2]
            frame_area = frame_h * frame_w
            
            # User position (bottom center of frame)
            user_x = frame_w // 2
            user_y = frame_h - 30
            
            # Run YOLO inference
            results = model(frame, device=INFERENCE_DEVICE, conf=MODEL_CONF_PREFILTER)[0]
            
            # Draw all detections
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                obj_w = x2 - x1
                obj_h = y2 - y1
                object_area = obj_w * obj_h
                rel_dist = object_area / frame_area
                
                cls = int(box.cls[0])
                label = model.names[cls]
                confidence = float(box.conf[0])
                
                # Color based on class
                color = (0, 255, 0)  # Green default
                if label.lower() == "door":
                    color = (0, 165, 255)  # Orange for door
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                text = f"{label} ({confidence:.2f})"
                cv2.putText(frame, text, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Draw navigation arrow for doors
                if label.lower() == "door":
                    # Draw line from user to door
                    cv2.line(frame, (user_x, user_y), (cx, cy), (255, 0, 0), 3)
                    # Draw arrow
                    cv2.arrowedLine(frame, (user_x, user_y), (cx, cy), (0, 0, 255), 4, tipLength=0.1)
                    
                    # Calculate distance
                    door_pixel_width = obj_w
                    actual_distance = (0.9 * 800) / door_pixel_width if door_pixel_width > 0 else 0
                    
                    # Draw distance with background
                    distance_text = f"Door: {actual_distance:.2f}m"
                    text_size = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    
                    cv2.rectangle(frame, (cx - 50, cy - 40),
                                 (cx - 50 + text_size[0], cy - 40 + text_size[1]),
                                 (0, 0, 255), -1)
                    
                    cv2.putText(frame, distance_text, (cx - 50, cy - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Draw user position
            cv2.circle(frame, (user_x, user_y), 8, (0, 255, 255), -1)
            cv2.putText(frame, "USER", (user_x - 20, user_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw header
            cv2.putText(frame, f"Device: {INFERENCE_DEVICE} | Detections: {len(results.boxes)}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                   + frame_bytes + b'\r\n')
            
        except Exception as e:
            print(f"Error in visualization: {e}")
            continue
    
    cap.release()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    print("✓ Health check received from app")
    return jsonify({"status": "healthy", "model_loaded": True}), 200

@app.route('/video_feed')
def video_feed():
    """
    Stream live camera feed with detection visualization
    Returns: Multipart/x-mixed-replace video stream
    """
    return Response(generate_visualization_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect', methods=['POST'])
def detect_objects():
    """
    Detect objects in image frame
    Expected input: JSON with base64 encoded image
    Returns: List of detected objects with names, positions, distances
    """
    print("\n" + "="*60)
    print("📨 INCOMING REQUEST - Frame received from app")
    print("="*60)
    
    if custom_model is None:
        print(f"❌ YOLOv8{MODEL_VARIANT} model not loaded!")
        return jsonify({"error": f"YOLOv8{MODEL_VARIANT} model not loaded"}), 500
    
    request_start = time.time()
    
    try:
        # Get image from request
        data = request.get_json()
        
        if 'image' not in data:
            print("❌ No image in request!")
            return jsonify({"error": "No image provided"}), 400
        
        # Decode base64 image
        decode_start = time.time()
        image_data = base64.b64decode(data['image'])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        decode_time = (time.time() - decode_start) * 1000
        
        if frame is None:
            print("❌ Failed to decode image - frame is None")
            return jsonify({"error": "Invalid image data"}), 400
        
        print(f"✓ Frame decoded successfully: {frame.shape}")
        print(f"⏱️  Decode time: {decode_time:.2f}ms")
        
        # ─── EDGE DETECTION: Analyze structural features ───
        edge_start = time.time()
        edges, edge_stats = detect_edges_sobel(frame, kernel_size=3)
        structural_features = analyze_structural_features(edges['binary'], edge_stats, frame.shape[0])
        edge_time = (time.time() - edge_start) * 1000
        
        print(f"🔍 EDGE DETECTION (Sobel):")
        print(f"  Total edge pixels: {edge_stats['total_edge_pixels']} ({edge_stats['edge_percentage']:.2f}% of frame)")
        print(f"  Edge strength: {edge_stats['mean_edge_strength']:.2f} (max: {edge_stats['max_edge_strength']})")
        print(f"  Obstruction level: {structural_features['obstruction_level']}")
        print(f"  Potential doorways: {structural_features['doorway_indicators']}")
        print(f"⏱️  Edge detection time: {edge_time:.2f}ms")
        
        # Run YOLOv8n model inference
        infer_start = time.time()
        
        all_boxes = []  # List of (cls_name, confidence, xyxy) tuples
        
        # YOLOv8n model: doors, furniture, humans, and indoor objects (18 classes after consolidation)
        if custom_model is not None:
            custom_results = custom_model(frame, conf=MODEL_CONF_PREFILTER, device=INFERENCE_DEVICE)[0]
            
            # 🔴 DEBUG: Show what raw model outputs
            print(f"\n🔍 RAW MODEL OUTPUT (before any filtering):")
            print(f"   Total detections at conf≥{MODEL_CONF_PREFILTER:.2f}: {len(custom_results.boxes)}")
            
            if len(custom_results.boxes) > 0:
                # Group by class for clarity
                by_class = {}
                for box in custom_results.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = custom_model.names[cls_id]
                    conf = float(box.conf[0])
                    
                    if cls_name not in by_class:
                        by_class[cls_name] = []
                    by_class[cls_name].append(conf)
                
                # Print grouped by class
                for cls_name in sorted(by_class.keys()):
                    confs = by_class[cls_name]
                    max_conf = max(confs)
                    avg_conf = sum(confs) / len(confs)
                    print(f"   {cls_name:20} - Count: {len(confs):2d} | Max: {max_conf:.3f} | Avg: {avg_conf:.3f}")
            else:
                print(f"   ⚠️  NO RAW DETECTIONS - model found nothing in this frame")
            
            # Convert detections
            for box in custom_results.boxes:
                cls_id = int(box.cls[0])
                xyxy = box.xyxy[0]
                # Ultralytics returns torch tensors; convert once so downstream logic is pure-Python.
                if hasattr(xyxy, "tolist"):
                    xyxy = xyxy.tolist()
                all_boxes.append({
                    'name': custom_model.names[cls_id],
                    'conf': float(box.conf[0]),
                    'xyxy': [float(v) for v in xyxy],
                    'source': 'yolov8n'
                })
        
        infer_time = (time.time() - infer_start) * 1000
        print(f"⏱️  TIMING | YOLOv8n inference: {infer_time:.2f}ms | Raw detections: {len(all_boxes)}")
        
        # ─── DIAGNOSTIC (optional): Show what YOLOv8n is detecting at low conf ───
        if ENABLE_RAW_DIAGNOSTIC:
            print("\n" + "="*60)
            print(f"🔍 RAW MODEL OUTPUT - What YOLOv8n sees at conf≥{MODEL_CONF_PREFILTER:.2f}:")
            print("="*60)
            
            if custom_model is not None:
                custom_diagnostic = custom_model(frame, conf=MODEL_CONF_PREFILTER, device=INFERENCE_DEVICE)[0]
                print(f"YOLOv8N: {len(custom_diagnostic.boxes)} detections at conf≥{MODEL_CONF_PREFILTER:.2f}")
                if len(custom_diagnostic.boxes) > 0:
                    for box in custom_diagnostic.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        print(f"  ✓ {custom_model.names[cls_id]:20} conf={conf:.4f}")
                else:
                    print("  ❌ No detections")
            
            print("="*60 + "\n")
        
        # ─── FIX 3: NORMALIZE DOOR NAMES EARLY (before filtering) ───
        for binfo in all_boxes:
            original_name = binfo['name']
            if binfo['name'].lower() in ["door", "glass door", "wooden door", "wooden entrance", "entrance", "wooden entrance door"]:
                binfo['name'] = "Door"  # Normalize all door variants to single name
            # ─── NORMALIZE PERSON/HUMAN NAMES ───
            elif binfo['name'].lower() in ["person", "human", "humans"]:  # Consolidated: "humans" merged into "human"
                binfo['name'] = "human"  # Normalize all human variants to single name
            
            if original_name != binfo['name']:
                print(f"   🔄 CONSOLIDATED: '{original_name}' → '{binfo['name']}' (conf={binfo['conf']:.3f})")
        
        # ─── FIX 2: NMS DEDUPLICATION - Merge overlapping boxes ───
        def apply_nms(boxes, iou_threshold=0.5):
            """Remove duplicate detections from overlapping boxes (keep highest confidence)"""
            if not boxes:
                return boxes
            
            # Sort by confidence descending
            sorted_boxes = sorted(boxes, key=lambda x: x['conf'], reverse=True)
            keep = []
            
            for i, box_i in enumerate(sorted_boxes):
                should_keep = True
                x1i, y1i, x2i, y2i = [float(v) for v in box_i['xyxy']]
                area_i = (x2i - x1i) * (y2i - y1i)
                
                for box_k in keep:
                    x1k, y1k, x2k, y2k = [float(v) for v in box_k['xyxy']]
                    area_k = (x2k - x1k) * (y2k - y1k)
                    
                    # Calculate IoU (Intersection over Union)
                    x1_inter = max(x1i, x1k)
                    y1_inter = max(y1i, y1k)
                    x2_inter = min(x2i, x2k)
                    y2_inter = min(y2i, y2k)
                    
                    if x2_inter > x1_inter and y2_inter > y1_inter:
                        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
                        union_area = area_i + area_k - inter_area
                        iou = inter_area / union_area if union_area > 0 else 0
                        
                        if iou > iou_threshold:
                            print(f"  🗑️  NMS: Removed {box_i['name']} (conf={box_i['conf']:.3f}) - overlaps with kept {box_k['name']} (IoU={iou:.3f})")
                            should_keep = False
                            break
                
                if should_keep:
                    keep.append(box_i)
            
            return keep
        
        all_boxes = apply_nms(all_boxes, iou_threshold=0.5)
        print(f"📊 After NMS deduplication: {len(all_boxes)} boxes remain")
        
        # DEBUG: Show all detections before filtering
        if all_boxes:
            print(f"📊 ALL DETECTIONS BEFORE CONFIDENCE FILTERING ({len(all_boxes)} total):")
            for idx, binfo in enumerate(all_boxes):
                print(f"  [{idx}] {binfo['name']:20} conf={binfo['conf']:.3f}")
            
            # 🔍 SPECIAL DEBUG: Show ALL human detections (even below threshold)
            human_detections = [b for b in all_boxes if b['name'].lower() == "human"]
            if human_detections:
                print(f"\n👤 HUMAN DETECTIONS FOUND ({len(human_detections)} total):")
                for hdet in human_detections:
                    print(f"  ✓ Human: conf={hdet['conf']:.3f} (will {'✅ PASS' if hdet['conf'] >= 0.35 else '❌ FAIL'} threshold of 0.35)")
            else:
                print(f"\n👤 NO HUMAN DETECTIONS - Model did not detect any humans in this frame")
                print(f"   Check: Lighting, distance, pose, or retrain with more human data")
        else:
            print(f"📭 No detections found in frame")
        
        h, w, _ = frame.shape
        center_x = w // 2
        
        detections = []
        humans = []
        door_detected = False
        
        # ─── FIX 4: DETAILED CONFIDENCE LOGGING & FIX 1: LOWERED THRESHOLDS ───
        for binfo in all_boxes:
            cls_name = consolidate_class_name(binfo['name'])  # Apply class consolidation
            confidence = binfo['conf']
            cls_lower = cls_name.lower()
            
            # FIX 4: Step 1 - Log raw detection
            print(f"  🔍 [YOLOV8N] {cls_name:20} conf={confidence:.3f}", end="")
            
            # FIX 1: IMPROVED thresholds based on consolidated classes
            # Class consolidation removes duplicates and plurals:
            # "chairs"→"chair", "humans"→"human", "round chair"→"chair", "glass door"→"door", "wooden entrance"→"door"
            # ADJUSTED THRESHOLDS FOR BETTER DETECTION (March 2025)
            threshold = 0.30  # Default: Standard YOLOv8 threshold
            
            # DOORS: Slightly lower for better detection (consolidated: door, glass door, wooden entrance)
            if cls_name == "Door" or cls_lower == "door":
                threshold = 0.25  # Door detection at 25% confidence
            
            # HUMANS: LOWERED threshold for better detection 🔴 KEY FIX
            # Previous: 0.48 was TOO HIGH → humans were filtered out
            # New: 0.35 allows more human detections while maintaining accuracy
            elif cls_lower == "human":
                threshold = 0.35  # ✅ IMPROVED: Human detection at 35% confidence (was 0.48)
            
            # TABLE: LOWERED for better furniture detection
            elif cls_lower == "table":
                threshold = 0.28  # ✅ IMPROVED: Table at 28% (was 0.30)
            
            # SOFA: Keep at standard
            elif cls_lower == "sofa":
                threshold = 0.30  # Sofa at standard 30%
            
            # CHAIRS: Consolidated to single class (was chair, chairs, round chair)
            elif cls_lower == "chair":
                threshold = 0.28  # ✅ IMPROVED: Chair at 28% (was 0.30)
            
            # WINDOWS: Slightly higher (harder to detect edge features)
            elif cls_lower == "window":
                threshold = 0.35  # Windows at 35%
            
            # OTHER custom objects: Standard threshold
            else:
                threshold = 0.30  # Default: 30%
            
            # FIX 4: Step 2 - Log threshold comparison and decision
            if confidence < threshold:
                print(f"  🔍 [YOLOV8N] {cls_name:20} conf={confidence:.3f} | threshold={threshold:.2f} | ❌ FILTERED (below threshold)")
                continue
            else:
                print(f"  🔍 [YOLOV8N] {cls_name:20} conf={confidence:.3f} | threshold={threshold:.2f} | ✅ PASSED")
            
            print(f"✅ Found {cls_name} (confidence: {confidence:.2f}) [{binfo['source']}]")
            
            x1, y1, x2, y2 = map(int, binfo['xyxy'])
            box_width = x2 - x1
            box_center = (x1 + x2) // 2
            box_center_y = (y1 + y2) // 2
            
            distance_m = estimate_distance(box_width, cls_name)
            
            detection = {
                "class": cls_name,
                "confidence": round(confidence, 2),
                "position": {
                    "x": box_center,
                    "y": box_center_y,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_x": box_center,
                    "center_y": box_center_y
                },
                "distance": distance_m,
                "width": box_width,
                "height": y2 - y1
            }
            
            detections.append(detection)
            print(f"  ✅ ADDED TO DETECTIONS: {cls_name} at distance={distance_m}m, confidence={confidence:.2f}")
            
            # Track humans separately for navigation logic
            if cls_lower == "human":
                humans.append({
                    "center": box_center,
                    "distance": distance_m
                })
                print(f"  👤 HUMAN TRACKED for navigation")
            
            # Track doors - check consolidated class name
            if cls_lower == "door":
                door_detected = True
                print(f"  🚪 DOOR MARKED AS DETECTED: {cls_name} at {distance_m}m (confidence: {confidence:.2f})")
        
        # Determine navigation instructions
        print(f"\n🔔 NAVIGATION LOGIC:")
        print(f"  Total detections (after filters): {len(detections)}")
        print(f"  Doors detected: {door_detected}")
        
        navigation = {
            "direction": "STRAIGHT",
            "arrow": None,
            "message": None,
            "popup": None
        }
        
        # Door detection logic - show popup for any detected door
        if door_detected:
            print(f"  ➡️  Door detected, generating popup...")
            door_obj = next((d for d in detections if d["class"] in ["Door"]), None)
            if door_obj:
                print(f"  ✓ DOOR POPUP CREATED for {door_obj['class']} at {door_obj['distance']}m (conf: {door_obj['confidence']})")
                navigation["popup"] = {
                    "type": "door",
                    "message": f"🚪 {door_obj['class']} detected at {door_obj['distance']} meters",
                    "question": "Do you want to go through this door?",
                    "distance": door_obj['distance'],
                    "confidence": door_obj['confidence'],
                    "position": door_obj["position"],
                    "options": ["Yes", "No"],
                    "action_url": "/handle_door_response"
                }
                navigation["arrow"] = "FORWARD"
                print(f"✓ Door popup triggered: {door_obj['distance']}m away (confidence: {door_obj['confidence']})")
        
        # Human detection and avoidance logic - show popup immediately
        if humans:
            # Sort by distance (closest first)
            humans.sort(key=lambda x: x['distance'])
            closest_human = humans[0]
            
            offset = closest_human['center'] - center_x
            
            if abs(offset) < 50:
                navigation["direction"] = "STOP"
                navigation["arrow"] = None
                navigation["message"] = "Human detected Deviate and go straight."
                navigation["popup"] = {
                    "type": "human",
                    "message": "Human detected Deviate and go straight.",
                    "distance": closest_human['distance']
                }
                print(f"✓ Human popup triggered (STOP): {closest_human['distance']}m away")
            elif offset < 0:
                navigation["direction"] = "RIGHT"
                navigation["arrow"] = "RIGHT"
                navigation["message"] = "👤 Human on left. Move right."
                navigation["popup"] = {
                    "type": "human",
                    "message": "👤 Human detected on left. Deviate right and go straight.",
                    "distance": closest_human['distance']
                }
                print(f"✓ Human popup triggered (RIGHT): {closest_human['distance']}m away")
            else:
                navigation["direction"] = "LEFT"
                navigation["arrow"] = "LEFT"
                navigation["message"] = "👤 Human on right. Move left."
                navigation["popup"] = {
                    "type": "human",
                    "message": "👤 Human detected on right. Deviate left and go straight.",
                    "distance": closest_human['distance']
                }
                print(f"✓ Human popup triggered (LEFT): {closest_human['distance']}m away")
        
        response = {
            "success": True,
            "detections": detections,
            "navigation": navigation,
            "frame_size": {
                "width": w,
                "height": h
            },
            "edge_detection": {
                "edge_percentage": edge_stats["edge_percentage"],
                "edge_strength": edge_stats["mean_edge_strength"],
                "obstruction_level": structural_features["obstruction_level"],
                "potential_doorways": structural_features["doorway_indicators"],
                "walls": structural_features["walls"]
            }
        }
        
        total_time = (time.time() - request_start) * 1000
        popup_info = "none" if not navigation['popup'] else f"{navigation['popup']['type']}"
        print(f"📤 RESPONSE SUMMARY:")
        print(f"  Detections sent: {len(detections)}")
        if detections:
            print(f"  Classes: {', '.join([d['class'] for d in detections])}")
        print(f"  Popup type: {popup_info}")
        if navigation['popup']:
            print(f"  Popup message: {navigation['popup'].get('message', 'no message')}")
            print(f"  Popup distance: {navigation['popup'].get('distance', 'no distance')}")
        print(f"  ⏱️  Total time: {total_time:.2f}ms\n")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in detection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/handle_door_response', methods=['POST'])
def handle_door_response():
    """
    Handle user's response to door popup
    Expected input: JSON with user_response and optional door_info
    """
    print("\n" + "="*60)
    print("🚪 DOOR RESPONSE RECEIVED")
    print("="*60)
    
    try:
        data = request.get_json()
        user_response = data.get("user_response", "no").lower()
        door_class = data.get("door_class", "Door")
        door_distance = data.get("door_distance", 0)
        
        print(f"User response: {user_response}")
        print(f"Door type: {door_class}")
        print(f"Distance: {door_distance}m")
        
        if user_response == "yes":
            response = {
                "success": True,
                "action": "proceed",
                "direction": "STRAIGHT",
                "message": f"✓ Proceeding through {door_class}...",
                "navigation": {
                    "direction": "STRAIGHT",
                    "arrow": "FORWARD",
                    "next_steps": "Navigate through door opening"
                }
            }
            print("✓ User chose to go through door")
        else:
            response = {
                "success": True,
                "action": "avoid",
                "direction": "TURN_AROUND",
                "message": "✗ Finding alternate route...",
                "navigation": {
                    "direction": "TURN_AROUND",
                    "arrow": "BACKWARD",
                    "next_steps": "Searching for alternative path"
                }
            }
            print("✗ User chose not to go through door")
        
        print("="*60 + "\n")
        return jsonify(response), 200
    
    except Exception as e:
        print(f"Error handling door response: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/edge_detection', methods=['POST'])
def edge_detection_endpoint():
    """
    Dedicated edge detection endpoint
    Analyzes structural features (walls, doorways, obstacles)
    Returns edge detection data and structural analysis
    """
    print("\n" + "="*60)
    print("🔍 EDGE DETECTION REQUEST RECEIVED")
    print("="*60)
    
    try:
        data = request.get_json()
        
        if 'image' not in data:
            print("❌ No image in request!")
            return jsonify({"error": "No image provided"}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            print("❌ Failed to decode image")
            return jsonify({"error": "Invalid image data"}), 400
        
        print(f"✓ Frame decoded: {frame.shape}")
        
        # Perform edge detection
        edge_start = time.time()
        edges, edge_stats = detect_edges_sobel(frame, kernel_size=3)
        structural_features = analyze_structural_features(edges['binary'], edge_stats, frame.shape[0])
        edge_time = (time.time() - edge_start) * 1000
        
        print(f"✅ Edge detection completed in {edge_time:.2f}ms")
        print(f"  Edge density: {edge_stats['edge_percentage']:.2f}%")
        print(f"  Obstruction: {structural_features['obstruction_level']}")
        print(f"  Doorways detected: {structural_features['doorway_indicators']}")
        
        # Generate base64 encoded edge visualization
        edge_vis = cv2.cvtColor(edges['binary'], cv2.COLOR_GRAY2BGR)
        ret, edge_buffer = cv2.imencode('.jpg', edge_vis, [cv2.IMWRITE_JPEG_QUALITY, 85])
        edge_base64 = base64.b64encode(edge_buffer).decode('utf-8') if ret else None
        
        response = {
            "success": True,
            "edge_stats": {
                "total_edge_pixels": edge_stats["total_edge_pixels"],
                "edge_percentage": edge_stats["edge_percentage"],
                "max_edge_strength": edge_stats["max_edge_strength"],
                "mean_edge_strength": edge_stats["mean_edge_strength"]
            },
            "structural_features": {
                "obstruction_level": structural_features["obstruction_level"],
                "potential_doorways": structural_features["doorway_indicators"],
                "walls": structural_features["walls"]
            },
            "edge_map": edge_base64,
            "processing_time_ms": round(edge_time, 2)
        }
        
        print("="*60 + "\n")
        return jsonify(response), 200
    
    except Exception as e:
        print(f"❌ Error in edge detection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/edge_visualization')
def edge_visualization():
    """
    Live edge detection visualization stream
    Real-time Sobel edge detection with structural analysis
    """
    def generate_edge_frames():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("📹 Edge detection visualization stream started")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                # Perform edge detection
                edges, edge_stats = detect_edges_sobel(frame, kernel_size=3)
                structural_features = analyze_structural_features(edges['binary'], edge_stats, frame.shape[0])
                
                # Create visualization combining edges and structural info
                vis = cv2.cvtColor(edges['binary'], cv2.COLOR_GRAY2BGR)
                
                # Overlay frame at reduced opacity for context
                vis = cv2.addWeighted(vis, 0.6, cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 
                                                           cv2.COLOR_GRAY2BGR), 0.4, 0)
                
                # Add text overlays
                h, w = vis.shape[:2]
                
                # Header info
                cv2.putText(vis, f"SOBEL EDGE DETECTION | Density: {edge_stats['edge_percentage']:.1f}%",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Obstruction level with color coding
                color = (0, 255, 0)  # Green for low
                if structural_features['obstruction_level'] == 'medium':
                    color = (0, 165, 255)  # Orange
                elif structural_features['obstruction_level'] == 'high':
                    color = (0, 0, 255)  # Red
                
                cv2.putText(vis, f"Obstruction: {structural_features['obstruction_level'].upper()}",
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Doorway info
                cv2.putText(vis, f"Potential Doorways: {structural_features['doorway_indicators']}",
                           (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Wall density info
                y_offset = 150
                cv2.putText(vis, "Wall Density:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                for wall in structural_features['walls']:
                    y_offset += 25
                    text = f"  {wall['location']}: {wall['edge_density']:.1f}%"
                    cv2.putText(vis, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                # Encode frame
                ret, buffer = cv2.imencode('.jpg', vis, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                       + frame_bytes + b'\r\n')
                
            except Exception as e:
                print(f"Error in edge visualization: {e}")
                continue
        
        cap.release()
    
    return Response(generate_edge_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("BACKEND SERVICE STARTUP")
    print("=" * 60)
    print("[1/4] PyTorch CUDA enabled - Using GPU if available")
    print("[2/4] Flask imported successfully")
    print("[3/4] Loading PyTorch and YOLO... (this may take 10-30 seconds)")
    print("     ✓ PyTorch imported")
    print(f"[3.1/4] Inference device selected: {INFERENCE_DEVICE}")
    print(f"[4/4] Loading YOLOv8{MODEL_VARIANT} model...")

    print(f"  📦 YOLOv8{MODEL_VARIANT} Model: {CUSTOM_MODEL_PATH} (exists: {os.path.exists(CUSTOM_MODEL_PATH)})")
    if custom_model:
        print(f"      ✅ YOLOv8{MODEL_VARIANT} model loaded ({len(custom_model.names)} classes)")
    
    print("=" * 60)
    print(f"✅ BACKEND READY - YOLOv8{MODEL_VARIANT} model loaded on port 5000")
    print("=" * 60)
    print()
    
    print("=" * 60)
    print(f"Starting YOLOv8{MODEL_VARIANT} Backend Service...")
    print("=" * 60)
    
    if custom_model:
        print(f"✅ YOLOv8{MODEL_VARIANT} Model: {len(custom_model.names)} classes")
        for idx, cls_name in custom_model.names.items():
            print(f"    {idx}: {cls_name}")
    else:
        print(f"❌ YOLOv8{MODEL_VARIANT} model failed to load!")
    
    print(f"\n🚀 Backend ready on port 5000 (YOLOv8{MODEL_VARIANT})")
    print(f"   Model Type: {MODEL_TYPE} (nano=fast, large=accurate)")
    print(f"   Switch models: set MODEL_TYPE environment variable")
    print(f"   Example: set MODEL_TYPE=large")
    print("=" * 60 + "\n")
    sys.stdout.flush()
    
    # Run Flask with output unbuffered
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
