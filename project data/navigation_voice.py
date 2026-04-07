# ==========================================================
# GNSS DENIED AI NAVIGATION SYSTEM (FINAL STABLE VERSION)
# ==========================================================

import cv2
import time
import argparse
import threading
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
# LOAD YOLO MODEL
# ==============================
print("Loading YOLO model...")
model = YOLO(args.model)

# ==============================
# OPEN VIDEO
# ==============================
cap = cv2.VideoCapture(args.video)

if not cap.isOpened():
    print("Error opening video file.")
    exit()

# ==============================
# TEXT TO SPEECH (FEMALE VOICE)
# ==============================
class VoiceGuide:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.lock = threading.Lock()

        voices = self.engine.getProperty("voices")
        for voice in voices:
            if "zira" in voice.name.lower() or "female" in voice.name.lower():
                self.engine.setProperty("voice", voice.id)
                break

        self.engine.setProperty("rate", 165)
        self.engine.setProperty("volume", 1.0)

    def speak(self, text):
        threading.Thread(target=self._run, args=(text,), daemon=True).start()

    def _run(self, text):
        with self.lock:
            self.engine.say(text)
            self.engine.runAndWait()


voice = VoiceGuide()

# ==============================
# DISTANCE ESTIMATION
# ==============================
KNOWN_WIDTH = 0.9
FOCAL_LENGTH = 800

def estimate_distance(pixel_width):
    if pixel_width == 0:
        return 0
    return round((KNOWN_WIDTH * FOCAL_LENGTH) / pixel_width, 2)

# ==============================
# CONTROL VARIABLES
# ==============================
last_door_time = 0
last_human_time = 0

print("Starting Navigation System...")
print("Press Q to exit.")

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

    door_present = False
    human_present = False

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id].lower()

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
        if cls_name in ["door", "glass door"]:
            door_present = True

        # ==========================
        # HUMAN DETECTION
        # ==========================
        if cls_name == "person":
            human_present = True

            offset = box_center - center_x

            # Draw arrow
            if abs(offset) < 50:
                cv2.arrowedLine(frame, (center_x, h-60),
                                (center_x, h-120),
                                (0,0,255), 5)
            elif offset < 0:
                cv2.arrowedLine(frame, (center_x, h-60),
                                (center_x+120, h-60),
                                (0,0,255), 5)
            else:
                cv2.arrowedLine(frame, (center_x, h-60),
                                (center_x-120, h-60),
                                (0,0,255), 5)

            cv2.putText(frame,
                        "Human is detected. Deviate and go straight.",
                        (50, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255,0,0), 3)

    current_time = time.time()

    # ==========================
    # DOOR VOICE (Every 5 sec)
    # ==========================
    if door_present and (current_time - last_door_time > 5):
        voice.speak("Door detected. Open and go.")
        last_door_time = current_time

    # ==========================
    # HUMAN VOICE (Every 3 sec)
    # ==========================
    if human_present and (current_time - last_human_time > 3):
        voice.speak("Human is detected. Deviate and go straight.")
        last_human_time = current_time

    cv2.imshow("GNSS Denied AI Navigation System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()