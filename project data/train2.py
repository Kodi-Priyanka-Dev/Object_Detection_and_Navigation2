from ultralytics import YOLO
import cv2
import os
import shutil
import torch


def main():
    # Automatically get current project folder
    BASE_PATH = os.getcwd()

    DATA_YAML = os.path.join(BASE_PATH, "dataset", "data.yaml")

    # ✅ Updated Video Path
    VIDEO_PATH = r"C:\Users\Priyanka\Documents\project data\input video 2.mp4"

    OUTPUT_FOLDER = os.path.join(BASE_PATH, "visualization")
    TRAIN_FOLDER = os.path.join(BASE_PATH, "runs")
    OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, "output_video.mp4")
    SAVED_MODEL_PATH = os.path.join(BASE_PATH, "best_model", "best.pt")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(TRAIN_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(BASE_PATH, "best_model"), exist_ok=True)

    print("Project Path:", BASE_PATH)
    print("Video Path:", VIDEO_PATH)
    print("Video Exists:", os.path.exists(VIDEO_PATH))

    if not os.path.exists(VIDEO_PATH):
        print("Video file not found! Check path.")
        return

    # Check CUDA availability
    if torch.cuda.is_available():
        print("CUDA GPU detected. Training on GPU...")
        device = "cuda"
    else:
        print("CUDA not available. Training on CPU...")
        device = "cpu"

    # Load base model
    model = YOLO("yolov8n.pt")

    # Train
    model.train(
        data=DATA_YAML,
        epochs=50,
        imgsz=640,
        batch=16,
        project=TRAIN_FOLDER,
        name="detect",
        device=device,
        amp=True,
        workers=0,
        cache=True,
    )

    print("Training completed.")

    best_model_path = os.path.join(TRAIN_FOLDER, "detect", "weights", "best.pt")

    if not os.path.exists(best_model_path):
        print("Best model not found!")
        return

    shutil.copy2(best_model_path, SAVED_MODEL_PATH)
    print("Best model saved at:", SAVED_MODEL_PATH)

    # Load best model
    model = YOLO(SAVED_MODEL_PATH)

    # 🔥 Use FFmpeg backend (important fix)
    cap = cv2.VideoCapture(VIDEO_PATH, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("Error opening video file.")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 30  # fallback FPS

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))

    print("Processing video... Press 'q' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, device=device)
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
    print("Best model saved at:", SAVED_MODEL_PATH)


if __name__ == "__main__":
    main()