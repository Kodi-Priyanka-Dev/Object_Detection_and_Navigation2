"""
DOOR DETECTION VISUALIZATION GUIDE
===================================

This script provides real-time door detection visualization using your trained
detect1892 model. Perfect for testing before deploying to the mobile app.

USAGE
─────
1. Ensure the model exists at: best_model/best.pt
2. Connect a webcam to your computer
3. Run the script:
   
   python door_detection_visualization.py

FEATURES
────────
✓ Real-time YOLO detection with multi-class support
✓ Door detection with distance estimation
✓ Navigation arrows pointing to detected doors
✓ Auto-disappear arrow when user gets close
✓ FPS counter and detection statistics
✓ Color-coded bounding boxes for different classes
✓ Direction indicators (TURN LEFT / TURN RIGHT / MOVE FORWARD)

DETECTION THRESHOLDS (Configurable)
───────────────────────────────────
Door:   10%   - High sensitivity (early warning)
Human:  50%   - High threshold (avoid false positives)
Other:  5%    - Low threshold for furniture

CONTROLS
────────
Press 'q' to quit

CLASSES DETECTED
────────────────
1. Door (Green)     - Primary target for navigation
2. Human (Orange)   - Obstacle detection
3. Tables (Blue)    - Furniture
4. Chairs (Magenta) - Furniture
5. Sofas (Cyan)     - Furniture
[And 15 other classes from the 20-class model]

DISTANCE ESTIMATION
───────────────────
Distance (cm) = (Reference Height × 100) / Bounding Box Height
Reference Height: 100 pixels (typical door height in frame)

ARROW BEHAVIOR
──────────────
✓ Arrow appears when door is detected
✓ Arrow disappears after 15 frames without door
✓ Arrow disappears when user is within 80 pixels of door center
✓ Direction label shows relative position:
  - "← TURN LEFT" if door is to the left
  - "TURN RIGHT →" if door is to the right
  - "↑ MOVE FORWARD" if door is straight ahead

TIPS FOR OPTIMAL DETECTION
──────────────────────────
1. Good lighting conditions (avoid backlighting)
2. Position door in frame center for best results
3. Maintain distance 1-3 meters from door
4. Avoid fast camera movements (smooth pans)
5. Test in similar environments to those in the app

INTEGRATION WITH FLUTTER APP
────────────────────────────
This visualization mimics the detection logic in:
- backend_service.py (Flask detection server)
- home_screen.dart (Flutter camera detection)
- sensor_navigation_service.dart (Sensor guidance)

To integrate:
1. Test detection accuracy with this script
2. Adjust CONFIDENCE_THRESHOLD values if needed
3. Deploy to backend_service.py
4. Run Flutter app to test on device

TROUBLESHOOTING
───────────────
Issue: Model not found
→ Ensure best_model/best.pt exists (from train_merged.py)

Issue: Camera not detected
→ Check camera availability: cv2.VideoCapture(0)
→ Try different camera indices: 0, 1, 2...

Issue: Low FPS
→ Reduce camera resolution in code
→ Use GPU detection: model(frame, device=0)

Issue: False positives
→ Increase CONFIDENCE_THRESHOLD values
→ Adjust DISTANCE_REF_HEIGHT based on your door

For more details, see:
- train_merged.py: Model training
- backend_service.py: Production detection server
- Navigation App/lib/screens/home_screen.dart: Flutter integration
"""
