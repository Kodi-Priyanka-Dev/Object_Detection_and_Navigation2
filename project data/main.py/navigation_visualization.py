# ==========================================================
# AI NAVIGATION VISUALIZATION WITH ARROW TO DOOR
# ==========================================================

import cv2
from ultralytics import YOLO
import torch
import os

# Load YOLO model
print("🔄 Loading YOLO model...")

# Determine model path - check multiple possible locations
model_paths = [
    "best_model/best.pt",
    "Navigation App/best_model/best.pt",
    "Navigation App/best.pt",
    os.path.join(os.path.dirname(__file__), "best_model", "best.pt"),
    os.path.join(os.path.dirname(__file__), "Navigation App", "best_model", "best.pt"),
    os.path.join(os.path.dirname(__file__), "Navigation App", "best.pt")
]

model_path = None
for path in model_paths:
    if os.path.exists(path):
        model_path = path
        print(f"✅ Found model at: {path}")
        break

if model_path is None:
    raise FileNotFoundError(f"Model not found. Searched: {model_paths}")

model = YOLO(model_path)

# Move model to GPU if available
INFERENCE_DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'
model.to(INFERENCE_DEVICE)
print(f"📍 Visualization Device: {INFERENCE_DEVICE}")

cap = cv2.VideoCapture(0)

# Set camera resolution for consistency
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

print("✅ Visualization started. Press ESC to exit.")

frame_count = 0
door_count = 0

while True:

    ret, frame = cap.read()
    if not ret:
        break

    frame_h, frame_w = frame.shape[:2]
    frame_area = frame_h * frame_w

    # User position (bottom center of frame)
    user_x = frame_w // 2
    user_y = frame_h - 30

    # Run YOLO inference
    results = model(frame, device=INFERENCE_DEVICE, conf=0.05)
    frame_count += 1

    door_detected = False

    for r in results:

        for box in r.boxes:

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            obj_w = x2 - x1
            obj_h = y2 - y1

            object_area = obj_w * obj_h

            # Relative distance (normalized by frame area)
            rel_dist = object_area / frame_area

            cls = int(box.cls[0])
            label = model.names[cls]
            confidence = float(box.conf[0])

            # Bounding box center
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # Draw bounding box
            color = (0, 255, 0)
            if label == "door":
                color = (0, 165, 255)  # Orange for door
                door_detected = True

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            text = f"{label} | Dist:{rel_dist:.3f} | Conf:{confidence:.2f}"
            cv2.putText(frame, text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # ==================================================
            # NAVIGATION ARROW TO DOOR
            # ==================================================

            if label == "door":

                door_count += 1

                # Draw navigation path line
                cv2.line(frame, (user_x, user_y), (cx, cy), (255, 0, 0), 3)

                # Draw arrow pointing to door (thicker, brighter red)
                cv2.arrowedLine(
                    frame,
                    (user_x, user_y),
                    (cx, cy),
                    (0, 0, 255),
                    4,
                    tipLength=0.1
                )

                # Calculate actual distance if using calibration
                door_pixel_width = obj_w
                actual_distance = (0.9 * 800) / door_pixel_width if door_pixel_width > 0 else 0

                # Display distance near door with background for readability
                distance_text = f"Door: {actual_distance:.2f}m (Rel: {rel_dist:.3f})"
                text_size = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                
                # Background rectangle
                cv2.rectangle(
                    frame,
                    (cx - 50, cy - 40),
                    (cx - 50 + text_size[0], cy - 40 + text_size[1]),
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    frame,
                    distance_text,
                    (cx - 50, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),  # White text on red background
                    2
                )

    # Draw user position at bottom center
    cv2.circle(frame, (user_x, user_y), 8, (0, 255, 255), -1)
    cv2.putText(frame, "USER", (user_x - 20, user_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Display header info
    header_text = f"Frame: {frame_count} | Doors Detected: {door_count} | Device: {INFERENCE_DEVICE}"
    cv2.putText(frame, header_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Display status
    status = "🟢 Door Detected" if door_detected else "⚫ Waiting for door..."
    cv2.putText(frame, status, (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if door_detected else (0, 0, 255), 2)

    cv2.imshow("AI Navigation Visualization", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

print(f"\n✅ Visualization complete. Total frames: {frame_count}, Doors detected: {door_count}")

cap.release()
cv2.destroyAllWindows()
