"""
Glass Door Navigation System with Human Detection
==================================================
Detects Glass Doors AND Humans - Routes navigation accordingly

Requirements:
    pip install ultralytics opencv-python numpy

Usage:
    python navic.py
"""

import cv2
import numpy as np
import argparse
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk
from ultralytics import YOLO

# For TTS
import pyttsx3
import queue


# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

CLASS_COLORS = {
    "glass door":       (0,   220, 220),
    "wooden entrance":  (0,   100, 255),
    "wall":             (50,  200,  50),
    "door":             (0,   220, 220),
    "person":           (220, 150,   0),
    "human":            (220, 150,   0),
    "humans":           (220, 150,   0),
    "table":            (180,  80, 180),
    "chair":            (50,  220, 180),
}
DEFAULT_COLOR = (180, 180, 180)

NAV_TARGETS = {"glass door", "door"}
HUMAN_TARGETS = {"person", "human"}

KNOWN_WIDTH_M   = 1.0
FOCAL_LENGTH_PX = 600


# ─────────────────────────────────────────────────────────────
# DISTANCE ESTIMATION
# ─────────────────────────────────────────────────────────────

def estimate_distance(bbox_width_px: int) -> float:
    if bbox_width_px <= 0:
        return 0.0
    return round((KNOWN_WIDTH_M * FOCAL_LENGTH_PX) / bbox_width_px, 2)


# ─────────────────────────────────────────────────────────────
# DIRECTIONAL ARROWS - HUMAN AVOIDANCE
# ─────────────────────────────────────────────────────────────

def draw_arrow_left(frame, x, y, size=50, color=(0, 165, 255), thickness=4):
    """Draw LEFT arrow with forward component"""
    # Diagonal arrow going left and slightly up
    cv2.arrowedLine(frame, (x + size, y + size // 2), (x - size, y - size), 
                    color, thickness, tipLength=0.3)
    # Forward arrow
    cv2.arrowedLine(frame, (x - size, y - size), (x, y - size - 20),
                    color, thickness - 1, tipLength=0.25)

def draw_arrow_straight(frame, x, y, size=60, color=(0, 255, 0), thickness=4):
    """Draw STRAIGHT/FORWARD arrow"""
    cv2.arrowedLine(frame, (x, y + size), (x, y - size), color, thickness, tipLength=0.3)

def draw_arrow_right(frame, x, y, size=50, color=(255, 165, 0), thickness=4):
    """Draw RIGHT arrow with forward component"""
    # Diagonal arrow going right and slightly up
    cv2.arrowedLine(frame, (x - size, y + size // 2), (x + size, y - size), 
                    color, thickness, tipLength=0.3)
    # Forward arrow
    cv2.arrowedLine(frame, (x + size, y - size), (x, y - size - 20),
                    color, thickness - 1, tipLength=0.25)

def draw_avoid_symbol(frame, x, y, size=50, color=(0, 0, 255), thickness=4):
    """Draw AVOID/STOP symbol"""
    # Draw X symbol
    cv2.line(frame, (x - size, y - size), (x + size, y + size), color, thickness)
    cv2.line(frame, (x + size, y - size), (x - size, y + size), color, thickness)
    # Circle around it
    cv2.circle(frame, (x, y), size + 5, color, thickness)

def get_direction_for_human(frame_width, human_center_x):
    """
    Determine navigation direction based on human position in frame.
    
    Logic:
      - Human from LEFT (x < 1/3)  → DEVIATE RIGHT + GO STRAIGHT
      - Human from CENTER (1/3 < x < 2/3) → STOP/AVOID
      - Human from RIGHT (x > 2/3) → DEVIATE LEFT + GO STRAIGHT
    """
    left_third = frame_width // 3
    right_third = (2 * frame_width) // 3
    
    if human_center_x < left_third:
        return "DEVIATE RIGHT & GO STRAIGHT"  # Human on left, deviate right
    elif human_center_x > right_third:
        return "DEVIATE LEFT & GO STRAIGHT"   # Human on right, deviate left
    else:
        return "STOP - HUMANS DETECTED"       # Human blocking center path

class GlassDoorPopup:
    """
    Tkinter dialog matching the screenshot:
      Title  : Glass Door Detected
      Body   : A Glass Door is X.XXm away.
               Do you want to open and go through?
      Buttons: Yes | No
    """

    def __init__(self, distance_m: float, on_yes=None, on_no=None):
        self.on_yes     = on_yes
        self.on_no      = on_no
        self._root      = None
        self.distance_m = distance_m

    def show(self):
        """Run in a separate thread so OpenCV loop is not blocked."""
        t = threading.Thread(target=self._build, daemon=True)
        t.start()

    def _build(self):
        self._root = tk.Tk()
        root = self._root
        root.title("Door Detected")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.configure(bg="#f0f0f0")

        # Center on screen
        w, h = 340, 170
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        # ── Icon + Title row ──────────────────────────────────
        top_frame = tk.Frame(root, bg="#f0f0f0")
        top_frame.pack(fill="x", padx=16, pady=(14, 4))

        icon_canvas = tk.Canvas(top_frame, width=32, height=32,
                                bg="#f0f0f0", highlightthickness=0)
        icon_canvas.pack(side="left")
        icon_canvas.create_oval(2, 2, 30, 30, fill="#4a90d9", outline="")
        icon_canvas.create_text(16, 16, text="?", fill="white",
                                font=("Arial", 14, "bold"))

        tk.Label(top_frame, text="Door Detected",
                 font=("Arial", 12, "bold"),
                 bg="#f0f0f0", fg="#222222").pack(side="left", padx=10)

        # ── Separator ─────────────────────────────────────────
        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=14, pady=4)

        # ── Body text ─────────────────────────────────────────
        body_frame = tk.Frame(root, bg="#f0f0f0")
        body_frame.pack(fill="x", padx=20, pady=4)

        tk.Label(body_frame,
                 text=f"A Door is {self.distance_m}m away.",
                 font=("Arial", 11), bg="#f0f0f0", fg="#333333").pack(anchor="w")
        tk.Label(body_frame,
                 text="Do you want to open and go through?",
                 font=("Arial", 11), bg="#f0f0f0", fg="#333333").pack(anchor="w")

        # ── Buttons ───────────────────────────────────────────
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(anchor="e", padx=16, pady=(8, 14))

        tk.Button(btn_frame, text="Yes", width=8,
                  font=("Arial", 10, "bold"),
                  bg="#e8f0fe", fg="#1a5fa8",
                  relief="groove", cursor="hand2",
                  command=self._yes).pack(side="left", padx=(0, 6))

        tk.Button(btn_frame, text="No", width=8,
                  font=("Arial", 10),
                  bg="#e1e1e1", fg="#333333",
                  relief="groove", cursor="hand2",
                  command=self._no).pack(side="left")

        root.protocol("WM_DELETE_WINDOW", self._no)
        root.mainloop()

    def _yes(self):
        if self.on_yes:
            self.on_yes()
        if self._root:
            self._root.destroy()

    def _no(self):
        if self.on_no:
            self.on_no()
        if self._root:
            self._root.destroy()


# ─────────────────────────────────────────────────────────────
# TKINTER POPUP — "Human Detected"
# ─────────────────────────────────────────────────────────────

class HumanDetectedPopup:
    """
    Simple popup for human detection (normal window, no alerts)
    """

    def __init__(self, message: str = "Human is detected! Deviate and go straight", on_ok=None):
        self.on_ok = on_ok
        self._root = None
        self.message = message

    def show(self):
        """Run in a separate thread so OpenCV loop is not blocked."""
        t = threading.Thread(target=self._build, daemon=True)
        t.start()

    def _build(self):
        self._root = tk.Tk()
        root = self._root
        root.title("Notification")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.configure(bg="#f0f0f0")

        # Center on screen
        w, h = 380, 160
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        # ── Body text ─────────────────────────────────────────
        body_frame = tk.Frame(root, bg="#f0f0f0")
        body_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(body_frame,
                 text=self.message,
                 font=("Arial", 12),
                 bg="#f0f0f0", 
                 fg="#333333",
                 wraplength=340,
                 justify="center").pack(anchor="center", expand=True)

        # ── Button ─────────────────────────────────────────────
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(anchor="center", pady=(0, 16))

        tk.Button(btn_frame, text="OK", width=12,
                  font=("Arial", 10),
                  bg="#e1e1e1", 
                  fg="#333333",
                  relief="groove", 
                  cursor="hand2",
                  command=self._ok).pack(side="left")

        root.protocol("WM_DELETE_WINDOW", self._ok)
        root.mainloop()

    def _ok(self):
        if self.on_ok:
            self.on_ok()
        if self._root:
            self._root.destroy()


# ─────────────────────────────────────────────────────────────
# POPUP MANAGER — single popup with cooldown
# ─────────────────────────────────────────────────────────────

class PopupManager:
    def __init__(self, cooldown_sec: float = 8.0):
        self.cooldown       = cooldown_sec
        self._last: dict    = {}
        self._popup_open    = False
        self._user_response = None
        self._human_popup_open = False
        self._human_last = 0

    def try_trigger(self, cls: str, distance_m: float) -> bool:
        """Fire popup only if cooldown expired and no popup currently open."""
        if self._popup_open:
            return False
        now = time.time()
        if now - self._last.get(cls, 0) < self.cooldown:
            return False

        self._last[cls] = now
        self._popup_open = True
        self._user_response = None

        def on_yes():
            self._user_response = 'yes'
            self._popup_open    = False
            print(f"[USER] Yes — navigating through {cls}")

        def on_no():
            self._user_response = 'no'
            self._popup_open    = False
            print(f"[USER] No — skipping {cls}")

        popup = GlassDoorPopup(distance_m, on_yes=on_yes, on_no=on_no)
        popup.show()
        return True

    def try_trigger_human(self, message: str) -> bool:
        """Fire human detection popup with simple message."""
        if self._human_popup_open:
            return False
        now = time.time()
        if now - self._human_last < 3.0:  # 3 second cooldown for human alerts
            return False

        self._human_last = now
        self._human_popup_open = True

        def on_ok():
            self._human_popup_open = False
            print(f"[SYSTEM] {message}")

        popup = HumanDetectedPopup(message=message, on_ok=on_ok)
        popup.show()
        return True

    @property
    def last_response(self):
        return self._user_response


# ─────────────────────────────────────────────────────────────
# CV DRAWING
# ─────────────────────────────────────────────────────────────

def draw_bbox(frame, x1, y1, x2, y2, label, conf, color):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label_str = f"{label}  {conf:.2f}"
    (tw, th), _ = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 12, y1), color, -1)
    cv2.putText(frame, label_str, (x1 + 6, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)


def draw_distance_box(frame, distance_m: float):
    text = f"Distance: {distance_m} m"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
    pad = 10
    cv2.rectangle(frame, (8, 8), (8 + tw + pad * 2, 8 + th + pad * 2),
                  (0, 200, 200), -1)
    cv2.putText(frame, text, (8 + pad, 8 + th + pad),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)


def draw_door_icon(frame, cx: int, cy: int, size: int = 55):
    hw = size // 2
    hh = int(size * 0.7)
    cv2.rectangle(frame, (cx - hw, cy - hh), (cx + hw, cy + hh),
                  (0, 220, 220), 3)
    cv2.arrowedLine(frame, (cx - hw + 6, cy), (cx + hw + 22, cy),
                    (0, 220, 220), 4, tipLength=0.35)


def draw_action_banner(frame, text: str, cy_center: int, w: int):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
    pad_x, pad_y = 24, 12
    rx1 = w // 2 - tw // 2 - pad_x
    rx2 = w // 2 + tw // 2 + pad_x
    ry1 = cy_center - th // 2 - pad_y
    ry2 = cy_center + th // 2 + pad_y

    overlay = frame.copy()
    cv2.rectangle(overlay, (rx1, ry1), (rx2, ry2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 220, 220), 2)
    cv2.putText(frame, text,
                (w // 2 - tw // 2, cy_center + th // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 220, 220), 3, cv2.LINE_AA)


def draw_outer_frame(frame):
    h, w = frame.shape[:2]
    margin = 20
    cv2.rectangle(frame, (margin, margin),
                  (w - margin, h - margin), (0, 200, 0), 2)


def draw_person_navigation(frame, px1, py1, px2, py2):
    """
    When a person is detected:
      Step 1 — Turn Left arrow  (←)
      Step 2 — Go Straight arrow (↑)
    Shown as two animated arrow steps beside the person bbox.
    """
    h, w = frame.shape[:2]
    t = time.time()

    # ── Arrow colors ─────────────────────────────────────────
    LEFT_COLOR     = (50,  50,  255)   # Red-ish  for Turn Left
    FORWARD_COLOR  = (50,  220,  50)   # Green    for Go Straight
    WARNING_COLOR  = (0,   140, 255)   # Orange   warning border

    # ── Highlight person bbox with warning color ──────────────
    cv2.rectangle(frame, (px1, py1), (px2, py2), WARNING_COLOR, 3)

    # ── Warning label above person ────────────────────────────
    warn_text = "! PERSON AHEAD"
    (tw, th), _ = cv2.getTextSize(warn_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (px1, py1 - th - 10), (px1 + tw + 12, py1), WARNING_COLOR, -1)
    cv2.putText(frame, warn_text, (px1 + 6, py1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

    # ── Direction panel position (bottom-left of frame) ──────
    panel_x  = 20
    panel_y  = h - 180
    panel_w  = 220
    panel_h  = 155

    # Panel background
    overlay = frame.copy()
    cv2.rectangle(overlay, (panel_x, panel_y),
                  (panel_x + panel_w, panel_y + panel_h), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    cv2.rectangle(frame, (panel_x, panel_y),
                  (panel_x + panel_w, panel_y + panel_h), WARNING_COLOR, 2)

    # Panel title
    cv2.putText(frame, "NAVIGATE AROUND", (panel_x + 10, panel_y + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WARNING_COLOR, 1, cv2.LINE_AA)

    # ── Step 1: Turn Left ─────────────────────────────────────
    pulse1 = int(6 * abs(np.sin(t * 3)))
    s1x = panel_x + 30 + pulse1
    s1y = panel_y + 65

    # Left arrow  ←
    cv2.arrowedLine(frame, (s1x + 50, s1y), (s1x, s1y),
                    LEFT_COLOR, 4, tipLength=0.4)
    cv2.putText(frame, "1. TURN LEFT", (panel_x + 70, s1y + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, LEFT_COLOR, 2, cv2.LINE_AA)

    # ── Step 2: Go Straight ───────────────────────────────────
    pulse2 = int(6 * abs(np.sin(t * 3 + 1.5)))
    s2x = panel_x + 55
    s2y = panel_y + 115 - pulse2

    # Up arrow  ↑
    cv2.arrowedLine(frame, (s2x, s2y + 30), (s2x, s2y),
                    FORWARD_COLOR, 4, tipLength=0.4)
    cv2.putText(frame, "2. GO STRAIGHT", (panel_x + 75, s2y + 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, FORWARD_COLOR, 2, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────

def run(video_path, model_path, conf_threshold, dist_trigger, cooldown):
    print(f"\n{'─'*52}")
    print(f"  Navigation and Obstacle Avoidance")
    print(f"{'─'*52}")
    print(f"  Video         : {video_path}")
    print(f"  Model         : {model_path}")
    print(f"  Conf threshold: {conf_threshold}")
    print(f"  Dist trigger  : {dist_trigger}m")
    print(f"  Cooldown      : {cooldown}s")
    print(f"{'─'*52}")
    print(f"  Q / ESC  — quit\n")


    # Initialize TTS engine
    class VoiceGuide:
        def __init__(self, rate: int = 150, volume: float = 0.9):
            self._queue        = queue.Queue()
            self._object_cache = {}
            self._text_cache   = {}
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate',   rate)
                self.engine.setProperty('volume', volume)
                voices = self.engine.getProperty('voices')
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                self._available = True
            except Exception as e:
                print(f"[TTS ERROR] Cannot initialise TTS: {e}")
                self.engine     = None
                self._available = False
            self._worker = threading.Thread(target=self._drain, daemon=True)
            self._worker.start()
        def speak(self, text, obj_id=None, cooldown=3.0, boost_volume=False, priority=False):
            if not self._available:
                return
            now = time.time()
            if text in self._text_cache and now - self._text_cache[text] < 2.0:
                return
            if obj_id and obj_id in self._object_cache:
                if now - self._object_cache[obj_id] < cooldown:
                    return
            self._text_cache[text] = now
            if obj_id:
                self._object_cache[obj_id] = now
            if priority:
                with self._queue.mutex:
                    self._queue.queue.clear()
            self._queue.put((text, boost_volume))
        def cleanup(self):
            if self._available:
                self._queue.put(None)
        def _drain(self):
            while True:
                item = self._queue.get()
                if item is None:
                    break
                text, boost = item
                try:
                    if boost:
                        self.engine.setProperty('volume', 1.0)
                        self.engine.setProperty('rate',   130)
                    else:
                        self.engine.setProperty('volume', 0.9)
                        self.engine.setProperty('rate',   150)
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[TTS worker error] {e}")
                finally:
                    self._queue.task_done()

    voice_guide = VoiceGuide()
    model     = YOLO(model_path)
    popup_mgr = PopupManager(cooldown_sec=cooldown)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open: {video_path}")
        sys.exit(1)

    fps, fps_timer, fps_count = 0.0, time.time(), 0
    frame_num  = 0
    nav_expire = 0.0

    # ── Output video writer ───────────────────────────────────
    import os
    output_dir  = r"C:\Users\Priyanka\Documents\project data\visualization"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "navigation_output.mp4")
    frame_w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_fps  = cap.get(cv2.CAP_PROP_FPS) or 30
    writer   = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        vid_fps,
        (frame_w, frame_h)
    )
    print(f"  Saving output : {output_path}\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_num += 1
        fps_count += 1
        now = time.time()
        if now - fps_timer >= 1.0:
            fps = fps_count / (now - fps_timer)
            fps_timer = now
            fps_count = 0

        h, w = frame.shape[:2]

        # ── YOLO inference ────────────────────────────────────
        results   = model(frame, verbose=False)[0]
        primary   = None
        best_conf = 0.0
        persons   = []   # collect all person detections this frame

        for box in results.boxes:
            conf     = float(box.conf[0])
            cls_id   = int(box.cls[0])
            cls_name = model.names[cls_id].lower()

            if conf < 0.25:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = CLASS_COLORS.get(cls_name, DEFAULT_COLOR)
            draw_bbox(frame, x1, y1, x2, y2, cls_name, conf, color)

            if cls_name in NAV_TARGETS and conf >= conf_threshold:
                if conf > best_conf:
                    best_conf = conf
                    primary   = (cls_name, conf, x1, y1, x2, y2)

            # ✅ ENHANCED: Detect both "person" and "human" labels
            if cls_name in HUMAN_TARGETS and conf >= conf_threshold:
                persons.append((x1, y1, x2, y2))

        # ── Primary nav target ────────────────────────────────
        if primary:
            cls_name, conf, x1, y1, x2, y2 = primary
            distance_m = estimate_distance(x2 - x1)

            draw_distance_box(frame, distance_m)
            draw_outer_frame(frame)
            draw_door_icon(frame, (x1 + x2) // 2, (y1 + y2) // 2 - 20)
            draw_action_banner(frame, "OPEN AND GO", (y1 + y2) // 2 + 50, w)

            if conf >= conf_threshold or distance_m <= dist_trigger:
                # Voice command for door detected
                voice_guide.speak(f"{cls_name.capitalize()} detected. Open and go.", obj_id=f"{cls_name}_door", cooldown=5.0)
                popup_mgr.try_trigger(cls_name, distance_m)

            nav_expire = now + 1.5

        # ── Person navigation directions ──────────────────────
        if persons:
            # Use the largest (closest) person detected
            largest = max(persons, key=lambda b: (b[2]-b[0]) * (b[3]-b[1]))
            px1, py1, px2, py2 = largest
            person_center_x = (px1 + px2) // 2
            
            # Get direction - only show popup, no extra symbols
            direction = get_direction_for_human(w, person_center_x)
            
            # Voice command for human detected
            voice_guide.speak("Human is detected. Deviate and go straight.", obj_id="human_detected", cooldown=5.0)
            # Show single popup notification
            popup_mgr.try_trigger_human("Human is detected! Deviate and go straight")

        # ── HUD ───────────────────────────────────────────────
        cv2.putText(frame,
                    f"Frame: {frame_num}  FPS: {fps:.1f}  Threshold: {conf_threshold}",
                    (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 130, 140), 1, cv2.LINE_AA)

        cv2.imshow("Navigation and Obstacle Avoidance", frame)
        writer.write(frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Output saved to: {output_path}")
    print("[INFO] Done.")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Glass Door Navigation (tkinter)")
    parser.add_argument("--video",        required=True,           help="Input video file")
    parser.add_argument("--model",        default="yolov8n.pt",    help="YOLO model weights")
    parser.add_argument("--conf",         type=float, default=0.6, help="Confidence threshold")
    parser.add_argument("--dist_trigger", type=float, default=5.0, help="Distance (m) to trigger popup")
    parser.add_argument("--cooldown",     type=float, default=8.0, help="Seconds between popups")
    args = parser.parse_args()

    run(
        video_path     = args.video,
        model_path     = args.model,
        conf_threshold = args.conf,
        dist_trigger   = args.dist_trigger,
        cooldown       = args.cooldown,
    )