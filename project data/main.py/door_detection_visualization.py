"""
Door Detection Visualization Script
====================================
Local testing tool for door detection using trained YOLO model
Shows real-time detection with navigation arrows and distance estimation
Uses the same detect1892 model as the backend service
"""

import cv2
import numpy as np
import time
from ultralytics import YOLO
from pathlib import Path

# ==============================
# LOAD YOLO MODEL
# ==============================
model_path = Path("best_model/best.pt")
if not model_path.exists():
    print(f"❌ Model not found at {model_path}")
    print("Please ensure best_model/best.pt exists")
    exit(1)

print(f"📦 Loading model from {model_path}...")
model = YOLO(str(model_path))
print(f"✅ Model loaded: {model.names}")

# ==============================
# CAMERA SETUP
# ==============================
print("\n📹 Initializing camera...")
cap = cv2.VideoCapture(0)

# Set camera resolution for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("❌ Failed to open camera")
    exit(1)

print("✅ Camera initialized")

# ==============================
# DETECTION CONFIGURATION
# ==============================
CONFIDENCE_THRESHOLD = {
    'door': 0.10,      # 10% - high sensitivity for doors
    'human': 0.50,     # 50% - high threshold to avoid false positives
    'table': 0.05,     # 5% - low threshold
    'sofa': 0.05,      # 5% - low threshold
    'chair': 0.05,     # 5% - low threshold
}

# Arrow display settings
FRAME_THRESHOLD = 15          # Frames to wait before arrow disappears
DIST_THRESHOLD = 80           # Pixel distance threshold (user too close)
DISTANCE_REF_HEIGHT = 100     # Reference height (pixels) = 100cm

# ==============================
# VARIABLES
# ==============================
arrow_active = False
missing_frames = 0
door_center = None
detection_history = {}
fps_counter = 0
fps_time = time.time()
current_fps = 0

# Color palette for different classes
COLOR_MAP = {
    'door': (0, 255, 0),       # Green
    'human': (0, 165, 255),    # Orange
    'table': (255, 0, 0),      # Blue
    'sofa': (255, 255, 0),     # Cyan
    'chair': (255, 0, 255),    # Magenta
}

# ==============================
# MAIN LOOP
# ==============================
print("\n🎬 Starting detection loop...")
print("Press 'q' to quit\n")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame")
        break

    frame_count += 1
    h, w = frame.shape[:2]

    # ──────────────────────────────────────────────────────────────
    # RUN YOLO DETECTION
    # ──────────────────────────────────────────────────────────────
    results = model(frame, conf=0.05, verbose=False)  # Raw predictions
    
    door_detected = False
    detections_current_frame = {
        'doors': [],
        'humans': [],
        'other': []
    }

    for r in results:
        boxes = r.boxes

        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = model.names[cls]

            # Get confidence threshold for this class
            threshold = CONFIDENCE_THRESHOLD.get(label, 0.5)

            # Skip if below threshold
            if conf < threshold:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = COLOR_MAP.get(label, (200, 200, 200))

            # ──────────────────────────────────────────────────────────────
            # DOOR DETECTION LOGIC
            # ──────────────────────────────────────────────────────────────
            if label == "door" and conf > CONFIDENCE_THRESHOLD['door']:
                door_detected = True
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                door_center = (cx, cy)
                
                detections_current_frame['doors'].append({
                    'box': (x1, y1, x2, y2),
                    'center': (cx, cy),
                    'conf': conf
                })

                # Draw thick green box for door
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(frame, f"DOOR {conf:.0%}", (x1, y1 - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Distance estimation (cm)
                box_height = y2 - y1
                if box_height > 0:
                    distance = int(DISTANCE_REF_HEIGHT * 100 / box_height)
                    cv2.putText(frame, f"Distance: {distance} cm", (x1, y2 + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # ──────────────────────────────────────────────────────────────
            # OTHER DETECTIONS
            # ──────────────────────────────────────────────────────────────
            elif label == "human" and conf > CONFIDENCE_THRESHOLD['human']:
                detections_current_frame['humans'].append({
                    'box': (x1, y1, x2, y2),
                    'conf': conf
                })
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"HUMAN {conf:.0%}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            else:
                if conf > CONFIDENCE_THRESHOLD.get(label, 0.5):
                    detections_current_frame['other'].append({
                        'box': (x1, y1, x2, y2),
                        'label': label,
                        'conf': conf
                    })
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                    cv2.putText(frame, f"{label.upper()} {conf:.0%}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # ──────────────────────────────────────────────────────────────
    # ARROW LOGIC
    # ──────────────────────────────────────────────────────────────

    if door_detected:
        arrow_active = True
        missing_frames = 0
    else:
        missing_frames += 1

    # Deactivate arrow if door not detected for threshold frames
    if missing_frames > FRAME_THRESHOLD:
        arrow_active = False
        door_center = None

    # Deactivate arrow if user is too close to door
    if door_center is not None and arrow_active:
        distance_to_center = abs(door_center[0] - w // 2)
        if distance_to_center < DIST_THRESHOLD:
            arrow_active = False
            cv2.putText(frame, "DOOR REACHED!", (w // 2 - 100, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

    # ──────────────────────────────────────────────────────────────
    # DRAW NAVIGATION ARROW
    # ──────────────────────────────────────────────────────────────

    if arrow_active and door_center is not None:
        # Arrow from bottom center to door center
        start_point = (w // 2, h - 50)
        end_point = door_center

        # Draw thick red arrow
        cv2.arrowedLine(frame, start_point, end_point, (0, 0, 255), 5, tipLength=0.3)

        # Add direction label
        dx = end_point[0] - start_point[0]
        if dx < -30:
            direction = "← TURN LEFT"
        elif dx > 30:
            direction = "TURN RIGHT →"
        else:
            direction = "↑ MOVE FORWARD"

        # Draw direction text
        text_size = cv2.getTextSize(direction, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = w // 2 - text_size[0] // 2
        cv2.rectangle(frame, (text_x - 5, h - 40), (text_x + text_size[0] + 5, h - 5),
                     (0, 0, 0), -1)
        cv2.putText(frame, direction, (text_x, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # ──────────────────────────────────────────────────────────────
    # FPS COUNTER
    # ──────────────────────────────────────────────────────────────
    fps_counter += 1
    elapsed = time.time() - fps_time
    if elapsed >= 1.0:
        current_fps = fps_counter / elapsed
        fps_counter = 0
        fps_time = time.time()

    # Draw FPS
    cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # ──────────────────────────────────────────────────────────────
    # STATUS INFO
    # ──────────────────────────────────────────────────────────────
    status_text = f"Doors: {len(detections_current_frame['doors'])} | Humans: {len(detections_current_frame['humans'])} | Other: {len(detections_current_frame['other'])}"
    cv2.putText(frame, status_text, (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # ──────────────────────────────────────────────────────────────
    # DISPLAY
    # ──────────────────────────────────────────────────────────────
    cv2.imshow("🚪 Door Detection Visualization", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n✋ Exiting...")
        break

print(f"\n📊 Processed {frame_count} frames")
cap.release()
cv2.destroyAllWindows()
print("✅ Done!")
