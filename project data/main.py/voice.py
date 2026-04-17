# ==========================================================
# GNSS DENIED AI NAVIGATION SYSTEM (FINAL CLEAN VERSION)
# ==========================================================

import cv2
import numpy as np
import time
import argparse
import threading
import queue
import pyttsx3
from ultralytics import YOLO

# ==============================
# ARGUMENTS
# ==============================
parser = argparse.ArgumentParser()
parser.add_argument("--video", type=str, required=True)
parser.add_argument("--model", type=str, required=True)
args = parser.parse_args()

# ==============================
# LOAD MODEL
# ==============================
print("Loading YOLO model...")
model = YOLO(args.model)

cap = cv2.VideoCapture(args.video)

if not cap.isOpened():
    print("Error opening video file.")
    exit()

# ==============================
# TEXT TO SPEECH CLASS (FIXED)
# ==============================
class VoiceGuide:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.last_spoken = {}
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self):
        """Single background thread that processes speech one at a time."""
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)   # Slightly slower = clearer
        engine.setProperty('volume', 1.0)
        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
            self.speech_queue.task_done()

    def speak(self, text, obj_id, cooldown=4.0):
        now = time.time()
        if obj_id in self.last_spoken:
            if now - self.last_spoken[obj_id] < cooldown:
                return
        self.last_spoken[obj_id] = now

        # Only add to queue if queue is empty (avoid buildup/overlap)
        if self.speech_queue.empty():
            self.speech_queue.put(text)

    def stop(self):
        self.speech_queue.put(None)


voice_guide = VoiceGuide()

# ==============================
# DISTANCE ESTIMATION
# ==============================
KNOWN_WIDTH = 0.9  # meters (approx door width)
FOCAL_LENGTH = 800  # adjust if needed

def estimate_distance(pixel_width):
    if pixel_width == 0:
        return 0
    return round((KNOWN_WIDTH * FOCAL_LENGTH) / pixel_width, 2)

# ==============================
# MAIN LOOP
# ==============================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)[0]

    h, w, _ = frame.shape
    center_x = w // 2

    persons = []
    door_detected = False

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        box_width = x2 - x1
        box_center = (x1 + x2) // 2

        distance_m = estimate_distance(box_width)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(frame, f"{cls_name} {distance_m}m",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0,255,0), 2)

        # ==========================
        # DOOR DETECTION
        # ==========================
        if cls_name.lower() in ["door", "glass door"]:
            door_detected = True

            popup_msg = f"Door detected at {distance_m} meters. Do you want to open and go?"

            cv2.putText(frame, popup_msg,
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0,0,255), 3)

            voice_guide.speak(
                popup_msg,
                obj_id=f"door_{int(distance_m)}",
                cooldown=5.0
            )

        # ==========================
        # HUMAN DETECTION
        # ==========================
        if cls_name.lower() == "person":
            persons.append((box_center, distance_m))

    # ==============================
    # HUMAN NAVIGATION LOGIC
    # ==============================
    if persons:
        persons.sort(key=lambda x: x[1])
        human_center, dist = persons[0]

        offset = human_center - center_x

        if abs(offset) < 50:
            direction = "STOP"
            arrow = None
            voice_text = "Stop. Human directly ahead."
        elif offset < 0:
            direction = "RIGHT"
            arrow = "RIGHT"
            voice_text = "Human detected on left. Deviate right and go straight."
        else:
            direction = "LEFT"
            arrow = "LEFT"
            voice_text = "Human detected on right. Deviate left and go straight."

        # Display popup
        cv2.putText(frame, voice_text,
                    (50, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255,0,0), 3)

        voice_guide.speak(
            voice_text,
            obj_id=f"human_{direction}",
            cooldown=4.0
        )

        # Draw arrow
        if arrow == "LEFT":
            cv2.arrowedLine(frame, (center_x, h-50),
                            (center_x-100, h-50),
                            (0,0,255), 5)
        elif arrow == "RIGHT":
            cv2.arrowedLine(frame, (center_x, h-50),
                            (center_x+100, h-50),
                            (0,0,255), 5)

    cv2.imshow("AI Navigation System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
voice_guide.stop()