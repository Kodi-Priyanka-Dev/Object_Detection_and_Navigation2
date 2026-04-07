"""
Multi-Model Flask Backend Service
==================================
Supports switching between Custom and YOLOv8n models.
Serves on port 5000.

Usage:
    python unified_server.py
    
Switch models via: POST /switch-model with {"model": "custom"} or {"model": "yolov8n"}
"""

print("=" * 60)
print("MULTI-MODEL BACKEND SERVICE STARTUP")
print("=" * 60)

import os
import sys
import time
import base64
import logging

print("[1/4] PyTorch CUDA enabled - Using GPU if available")

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    print("[2/4] Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import error: {e}")
    print("    Run: pip install flask flask-cors")
    sys.exit(1)

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
sys.stdout.flush()

print("[3/4] Loading PyTorch and YOLO...")
try:
    import torch
    from ultralytics import YOLO
    print("     ✓ PyTorch imported")
except Exception as e:
    print(f"❌ PyTorch import error: {e}")
    sys.exit(1)

DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'
print(f"[3.1/4] Inference device: {DEVICE}")

app = Flask(__name__)
CORS(app)

# ─── Model paths ──────────────────────────────────────
MODEL_PATHS = {
    "custom": os.path.join("..", "best_model", "best.pt"),
    "yolov8n": "yolov8n.pt"  # Will download if not present
}

CURRENT_MODEL_NAME = "custom"
model = None


def load_model(model_name):
    """
    Load model by name: 'custom' or 'yolov8n'
    If model doesn't exist, attempt to download it (for yolov8n)
    """
    global model, CURRENT_MODEL_NAME
    
    if model_name not in MODEL_PATHS:
        error_msg = f"Unknown model: {model_name}. Available: {list(MODEL_PATHS.keys())}"
        print(f"      ❌ {error_msg}")
        return False, error_msg
    
    model_path = MODEL_PATHS[model_name]
    print(f"\n[Loading] {model_name} from: {model_path}")
    print(f"      File exists: {os.path.exists(model_path)}")
    
    try:
        # Attempt to load model
        try:
            print(f"      Attempting to load from path...")
            model = YOLO(model_path)
            print(f"      ✅ {model_name} loaded from path")
        except Exception as load_error:
            # If loading fails and it's yolov8n, try to download
            if model_name == "yolov8n":
                print(f"      ⚠️  Model not found at {model_path}")
                print(f"      🔄 Attempting to download YOLOv8n automatically...")
                model = YOLO('yolov8n.pt')  # Auto-download from Ultralytics
                print(f"      ✅ YOLOv8n downloaded and loaded successfully!")
            elif model_name == "custom":
                # Custom model must exist
                error_msg = f"Custom model not found at {model_path}. Please ensure best_model/best.pt exists."
                print(f"      ❌ {error_msg}")
                raise load_error
            else:
                raise load_error
        
        # Move model to GPU if available
        if DEVICE.startswith('cuda'):
            model.to(DEVICE)
            model_device = next(model.model.parameters()).device
        else:
            model_device = 'cpu'
        
        CURRENT_MODEL_NAME = model_name
        print(f"      ✅ {model_name} loaded successfully!")
        print(f"      📍 Device: {model_device}")
        print(f"      📊 Classes: {len(model.names)}")
        return True, f"Model {model_name} loaded successfully"
    
    except Exception as e:
        error_msg = f"Failed to load {model_name}: {str(e)}"
        print(f"      ❌ {error_msg}")
        return False, error_msg


# Load default custom model
print(f"[4/4] Loading default model: custom")
success, msg = load_model("custom")

print("=" * 60)
if model:
    print(f"✅ MULTI-MODEL BACKEND READY on port 5000")
    print(f"   Current Model: {CURRENT_MODEL_NAME} ({len(model.names)} classes)")
    for idx, name in model.names.items():
        print(f"    {idx}: {name}")
else:
    print("⚠️  WARNING - Default model failed to load. Try switching models.")
print("=" * 60 + "\n")

# ─── Distance estimation ───────────────────────────────
OBJECT_WIDTHS = {
    "door": 0.9, "glass door": 0.9, "wooden entrance": 0.9,
    "human": 0.5, "humans": 0.5, "person": 0.5,
    "chair": 0.5, "chairs": 0.5, "round chair": 0.5,
    "sofa": 1.5, "couch": 1.5,
    "table": 1.2,
    "backpack": 0.35, "handbag": 0.3, "suitcase": 0.5, "bottle": 0.08,
}
FOCAL_LENGTH = 800


def estimate_distance(class_name, pixel_width):
    if pixel_width == 0:
        return 0
    known_w = OBJECT_WIDTHS.get(class_name.lower(), 0.5)
    return round((known_w * FOCAL_LENGTH) / pixel_width, 2)


# ─── Door classes (for popup) ──────────────────────────
DOOR_CLASSES = {"door", "glass door", "wooden entrance"}
HUMAN_CLASSES = {"human", "humans"}  # Only human classes, no generic person


@app.route('/health', methods=['GET'])
def health_check():
    print("✓ Health check received")
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "current_model": CURRENT_MODEL_NAME,
        "classes": len(model.names) if model else 0,
        "available_models": list(MODEL_PATHS.keys()),
    }), 200


@app.route('/switch-model', methods=['POST'])
def switch_model():
    """Switch between custom and yolov8n models"""
    try:
        data = request.get_json()
        model_name = data.get('model', 'custom').lower()
        
        success, msg = load_model(model_name)
        
        if success:
            print(f"✅ Switched to {model_name} model")
            return jsonify({
                "status": "switched",
                "current_model": CURRENT_MODEL_NAME,
                "classes": len(model.names),
                "message": msg
            }), 200
        else:
            print(f"❌ Failed to switch to {model_name}: {msg}")
            return jsonify({
                "status": "error", 
                "message": msg,
                "current_model": CURRENT_MODEL_NAME
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/detect', methods=['POST'])
def detect_objects():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    request_start = time.time()

    try:
        data = request.get_json()
        if 'image' not in data:
            return jsonify({"error": "No image provided"}), 400

        # Decode image
        image_data = base64.b64decode(data['image'])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"error": "Invalid image data"}), 400

        # Run detection with lower threshold (0.3) for better human detection
        results = model(frame, conf=0.3, device=DEVICE)[0]

        h, w, _ = frame.shape
        center_x = w // 2
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            confidence = float(box.conf[0])

            # NORMALIZE: person/Person -> Human
            if cls_name.lower() == "person":
                cls_name = "Human"

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            box_width = x2 - x1
            box_center_x = (x1 + x2) // 2
            box_center_y = (y1 + y2) // 2

            distance_m = estimate_distance(cls_name, box_width)

            detections.append({
                "class": cls_name,
                "confidence": round(confidence, 2),
                "position": {
                    "x": box_center_x,
                    "y": box_center_y,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "center_x": box_center_x,
                    "center_y": box_center_y,
                },
                "distance": distance_m,
                "width": box_width,
                "height": y2 - y1,
            })
            
            # Log specific detections
            if cls_name.lower() in HUMAN_CLASSES:
                if confidence >= 0.35:
                    print(f"  ✅ HUMAN DETECTED: {cls_name} | confidence={confidence:.2f} | distance={distance_m}m")
                else:
                    print(f"  ⏭️  Human filtered (low confidence): {cls_name} | confidence={confidence:.2f} (need >= 0.35)")
            elif cls_name.lower() in DOOR_CLASSES:
                print(f"  🚪 Door detected: {cls_name} | confidence={confidence:.2f} | distance={distance_m}m")

        # Navigation logic
        navigation = {
            "direction": "STRAIGHT",
            "arrow": None,
            "message": None,
            "popup": None,
        }

        # Door detection
        doors = [d for d in detections if d["class"].lower() in DOOR_CLASSES]
        if doors:
            doors.sort(key=lambda x: x["distance"])
            closest = doors[0]
            offset = closest["position"]["center_x"] - center_x

            if offset < -80:
                navigation["direction"] = "LEFT"
                navigation["arrow"] = "LEFT"
            elif offset > 80:
                navigation["direction"] = "RIGHT"
                navigation["arrow"] = "RIGHT"
            else:
                navigation["direction"] = "FORWARD"
                navigation["arrow"] = "FORWARD"

            navigation["popup"] = {
                "type": "door",
                "message": f"🚪 {closest['class']} detected at {closest['distance']}m",
                "question": "Do you want to go through this door?",
                "distance": closest["distance"],
                "confidence": closest["confidence"],
                "position": closest["position"],
                "options": ["Yes", "No"],
                "action_url": "/handle_door_response",
            }

        # Human detection - ONLY when confidence >= 0.35 (strict to avoid false positives)
        humans = [d for d in detections if d["class"].lower() in HUMAN_CLASSES and d["confidence"] >= 0.35]
        if humans and not doors:
            humans.sort(key=lambda x: x["distance"])
            closest = humans[0]
            offset = closest["position"]["center_x"] - center_x

            if abs(offset) < 100:
                navigation["direction"] = "STOP"
                navigation["popup"] = {
                    "type": "human",
                    "message": f"👤 Human directly ahead at {closest['distance']}m (confidence: {closest['confidence']})",
                    "distance": closest["distance"],
                }
            elif offset < 0:
                navigation["direction"] = "RIGHT"
                navigation["popup"] = {
                    "type": "human",
                    "message": f"👤 Human on left at {closest['distance']}m. Go right.",
                    "distance": closest["distance"],
                }
            else:
                navigation["direction"] = "LEFT"
                navigation["popup"] = {
                    "type": "human",
                    "message": f"👤 Human on right at {closest['distance']}m. Go left.",
                    "distance": closest["distance"],
                }

        total_ms = (time.time() - request_start) * 1000
        human_count = sum(1 for d in detections if d["class"].lower() in HUMAN_CLASSES)
        door_count = sum(1 for d in detections if d["class"].lower() in DOOR_CLASSES)
        print(f"📤 Total detections: {len(detections)} | Doors: {door_count} | Humans: {human_count} | Time: {total_ms:.0f}ms\n")

        return jsonify({
            "success": True,
            "detections": detections,
            "navigation": navigation,
            "frame_size": {"width": w, "height": h},
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/handle_door_response', methods=['POST'])
def handle_door_response():
    try:
        data = request.get_json()
        user_response = data.get('user_response', '').lower()
        door_class = data.get('door_class', 'door')
        door_distance = data.get('door_distance', 0)

        if user_response == 'yes':
            return jsonify({
                "action": "navigate",
                "message": f"Navigating through {door_class}",
                "voice": f"Navigating through {door_class} at {door_distance} meters",
            }), 200
        else:
            return jsonify({
                "action": "skip",
                "message": f"Skipping {door_class}",
                "voice": f"Skipping {door_class}",
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print(f"\n🚀 Multi-model backend on port 5000")
    print(f"   Switch models: POST /switch-model with {{'model': 'custom'|'yolov8n'}}")
    print(f"   Check health: GET /health")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
