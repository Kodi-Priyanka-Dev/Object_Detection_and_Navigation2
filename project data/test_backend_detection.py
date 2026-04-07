"""
Backend Service Integration Test
=================================
Tests the Flask backend service to verify detection is working correctly.
Send frames to the backend and receive detection results.

Usage:
    python test_backend_detection.py
"""

import cv2
import numpy as np
import requests
import json
import time
import base64
import os
from pathlib import Path

# ==============================
# CONFIGURATION
# ==============================
BACKEND_URL = os.getenv("BACKEND_URL", "http://10.26.67.141:5000/detect")  # Change IP if needed
CAMERA_INDEX = 0
FRAME_SKIP = 1  # Process every Nth frame (for performance)

print(f"""
╔════════════════════════════════════════════════════════════════╗
║         BACKEND DETECTION SERVICE TEST                         ║
║                                                                ║
║  This script tests the Flask backend by sending camera frames ║
║  and displaying the detection results in real-time.            ║
╚════════════════════════════════════════════════════════════════╝
""")

# ==============================
# OPEN CAMERA
# ==============================
print(f"📹 Opening camera {CAMERA_INDEX}...")
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"❌ Failed to open camera {CAMERA_INDEX}")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("✅ Camera opened\n")

# ==============================
# BACKEND CONNECTION
# ==============================
print(f"🌐 Testing backend connection to {BACKEND_URL}...")
try:
    response = requests.get(BACKEND_URL.replace("/detect", "/health"), timeout=2)
    print(f"✅ Backend is online\n")
except Exception as e:
    print(f"⚠️  Backend may not be running: {e}")
    print(f"   Start backend with: python Navigation App\\backend_service.py\n")

# ==============================
# DETECTION STATS
# ==============================
frame_count = 0
detections_count = 0
doors_count = 0
humans_count = 0
fps_time = time.time()
frame_time = 0
last_fps = 0

# ==============================
# MAIN LOOP
# ==============================
print("📊 Starting backend detection test...")
print("   Press 'q' to quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame")
        break

    frame_count += 1
    h, w = frame.shape[:2]

    # Skip frames for performance
    if frame_count % FRAME_SKIP != 0:
        continue

    # ──────────────────────────────────────────────────────────────
    # PREPARE FRAME FOR BACKEND
    # ──────────────────────────────────────────────────────────────
    
    # Encode frame to JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()

    # ──────────────────────────────────────────────────────────────
    # SEND TO BACKEND
    # ──────────────────────────────────────────────────────────────
    
    try:
        start_time = time.time()
        
        payload = {"image": base64.b64encode(frame_bytes).decode("utf-8")}
        response = requests.post(
            BACKEND_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )
        
        backend_latency = (time.time() - start_time) * 1000  # ms
        
        if response.status_code != 200:
            print(f"❌ Backend error: {response.status_code}")
            continue

        # ──────────────────────────────────────────────────────────────
        # PARSE RESPONSE
        # ──────────────────────────────────────────────────────────────
        
        data = response.json()
        
        detections = data.get('detections', [])
        navigation = (data.get('navigation', {}) or {}).get('direction', 'NONE')
        
        detections_count = len(detections)
        doors_count = sum(1 for d in detections if str(d.get('class', '')).lower() == 'door')
        humans_count = sum(1 for d in detections if str(d.get('class', '')).lower() == 'human')

        # ──────────────────────────────────────────────────────────────
        # DRAW DETECTIONS ON FRAME
        # ──────────────────────────────────────────────────────────────
        
        for det in detections:
            label = det.get('class', 'Unknown')
            confidence = det.get('confidence', 0)
            bbox = det.get('position', {}) or {}
            
            x1 = int(bbox.get('x1', 0))
            y1 = int(bbox.get('y1', 0))
            x2 = int(bbox.get('x2', 0))
            y2 = int(bbox.get('y2', 0))
            
            # Color based on class
            if label == 'Door':
                color = (0, 255, 0)  # Green
                thickness = 3
            elif label == 'Human':
                color = (0, 165, 255)  # Orange
                thickness = 2
            else:
                color = (200, 200, 200)  # Gray
                thickness = 1
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label
            text = f"{label} {confidence:.0%}"
            cv2.putText(frame, text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw distance if available
            if 'distance' in det:
                distance_text = f"Distance: {det['distance']} m"
                cv2.putText(frame, distance_text, (x1, y2 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # ──────────────────────────────────────────────────────────────
        # DRAW STATS
        # ──────────────────────────────────────────────────────────────
        
        # Header with latency
        header = f"Backend Latency: {backend_latency:.0f}ms | FPS: {last_fps:.1f}"
        cv2.putText(frame, header, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Detection summary
        summary = f"Detections: {detections_count} | Doors: {doors_count} | Humans: {humans_count}"
        cv2.putText(frame, summary, (10, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Navigation direction
        if navigation != 'NONE':
            nav_color = (0, 255, 255) if navigation in ['LEFT', 'RIGHT'] else (0, 255, 0)
            nav_text = f"Direction: {navigation}"
            cv2.putText(frame, nav_text, (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, nav_color, 2)

        # Calculate FPS
        elapsed = time.time() - fps_time
        if elapsed >= 1.0:
            last_fps = frame_count / elapsed
            frame_count = 0
            fps_time = time.time()

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        print(f"   Make sure backend is running!")
        cv2.putText(frame, "BACKEND NOT CONNECTED", (50, h // 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    except Exception as e:
        print(f"❌ Error: {e}")
        cv2.putText(frame, f"ERROR: {str(e)[:30]}", (10, h - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # ──────────────────────────────────────────────────────────────
    # DISPLAY
    # ──────────────────────────────────────────────────────────────
    
    cv2.imshow("🌐 Backend Detection Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n✋ Exiting...")
        break

print(f"\n📊 Test completed")
print(f"   Total frames processed: {frame_count}")
print(f"   Total detections: {detections_count}")

cap.release()
cv2.destroyAllWindows()
print("✅ Done!\n")
