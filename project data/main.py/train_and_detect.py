# ==============================
# ALL-IN-ONE YOLOv8 TRAIN + VIDEO DETECTION (SAFE VERSION)
# ==============================

# pip install ultralytics opencv-python

from ultralytics import YOLO
import cv2
import os

# ==============================
# AUTOMATIC PROJECT PATH
# ==============================

BASE_PATH = os.getcwd()

DATA_YAML = os.path.join(BASE_PATH, "dataset", "data.yaml")
VIDEO_PATH = os.path.join(BASE_PATH, "input_video.mp4.mp4")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "visualization")
OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, "output_video.mp4")

# Create visualization folder if not exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==============================
# STEP 1: TRAIN MODEL
# ==============================

if not os.path.exists(DATA_YAML):
    print("data.yaml not found at:", DATA_YAML)
    exit()

print("Starting YOLOv8 training...")

model = YOLO("yolov8n.pt")  # Pretrained nano model

model.train(
    data=DATA_YAML,
    epochs=50,
    imgsz=640,
    batch=8
)

print("Training completed.")

# ==============================
# STEP 2: LOAD BEST MODEL
# ==============================

best_model_path = os.path.join(BASE_PATH, "runs", "detect", "train", "weights", "best.pt")

if not os.path.exists(best_model_path):
    print("Best model not found at:", best_model_path)
    exit()

model = YOLO(best_model_path)
print("Model loaded successfully.")

# ==============================
# STEP 3: VIDEO DETECTION
# ==============================

if not os.path.exists(VIDEO_PATH):
    print("Input video not found at:", VIDEO_PATH)
    exit()

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("Error opening video file.")
    exit()

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

print("Processing video...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    annotated_frame = results[0].plot()

    out.write(annotated_frame)
    cv2.imshow("YOLOv8 Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("Detection completed.")
print("Output saved at:", OUTPUT_PATH)