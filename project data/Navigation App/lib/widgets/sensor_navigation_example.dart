// ─────────────────────────────────────────────────────────────────────────────
// SENSOR NAVIGATION INTEGRATION EXAMPLE
// ─────────────────────────────────────────────────────────────────────────────
// 
// This file demonstrates how to integrate the SensorNavigationHUD with your
// Flutter navigation app. It shows the complete setup, permissions, and usage.
//
// ─────────────────────────────────────────────────────────────────────────────

// ── STEP 1: pubspec.yaml — Add these dependencies ──────────────────────────────
// 
// Add to your pubspec.yaml:
//
// dependencies:
//   sensors_plus: ^4.0.2        # accelerometer, gyroscope, magnetometer
//   flutter_tts: ^4.0.2         # optional: TTS for voice commands
//
// Then run: flutter pub get
//
// ─────────────────────────────────────────────────────────────────────────────

// ── STEP 2: Android Permissions (android/app/src/main/AndroidManifest.xml) ────
//
// No special permissions required for sensors_plus!
// But optionally add these feature declarations:
//
// <manifest ...>
//   <uses-feature android:name="android.hardware.sensor.accelerometer" 
//                 android:required="false"/>
//   <uses-feature android:name="android.hardware.sensor.gyroscope" 
//                 android:required="false"/>
//   <uses-feature android:name="android.hardware.sensor.compass" 
//                 android:required="false"/>
// </manifest>
//
// ─────────────────────────────────────────────────────────────────────────────

// ── STEP 3: iOS Permissions (ios/Runner/Info.plist) ──────────────────────────
//
// Add to Info.plist:
//
// <key>NSMotionUsageDescription</key>
// <string>Used for navigation direction and sensor-based wayfinding</string>
//
// <key>NSLocationWhenInUseUsageDescription</key>
// <string>Used for compass heading and navigation</string>
//
// ─────────────────────────────────────────────────────────────────────────────

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'sensor_navigation_hud.dart';
import '../services/sensor_navigation_service.dart';

/// Example: Main navigation screen with sensor-based compass HUD
/// 
/// This demonstrates:
/// - Embedding SensorNavigationHUD in a camera/main screen
/// - Setting dynamic target headings (e.g., from door detection)
/// - Voice commands on direction changes
/// - Interactive heading picker (demo UI)
/// 
class SensorNavigationExample extends StatefulWidget {
  const SensorNavigationExample({Key? key}) : super(key: key);

  @override
  State<SensorNavigationExample> createState() => _SensorNavigationExampleState();
}

class _SensorNavigationExampleState extends State<SensorNavigationExample> {
  final FlutterTts _tts = FlutterTts();
  String? _lastSpokenKey;

  // ── User should walk toward this heading (0–360°) ────────────────────────────
  // Set from door detection, map route, or other navigation logic
  // Examples:
  //   0° = North
  //   90° = East
  //   180° = South
  //   270° = West
  double? _targetHeading = 90.0;

  @override
  void initState() {
    super.initState();
    _initTts();
  }

  Future<void> _initTts() async {
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      body: Stack(
        children: [
          // ── CAMERA PREVIEW (placeholder) ──────────────────────────────────
          Container(
            color: const Color(0xFF0D1B2A),
            child: Center(
              child: Text(
                'CAMERA PREVIEW\n(CameraPreview widget goes here)',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.3),
                  fontSize: 16,
                ),
              ),
            ),
          ),

          // ── SENSOR NAVIGATION HUD — Overlay at bottom ─────────────────────
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SensorNavigationHUD(
              targetHeading: _targetHeading,
              showGuidance: true,
              onNavigationStateChanged: _onNavigationStateChanged,
            ),
          ),

          // ── TARGET HEADING PICKER — Demo UI (top right) ────────────────────
          Positioned(
            top: 48,
            right: 16,
            child: _buildHeadingPicker(),
          ),

          // ── SYSTEM INFO — Top left ─────────────────────────────────────────
          Positioned(
            top: 48,
            left: 16,
            child: _buildSystemInfo(),
          ),
        ],
      ),
    );
  }

  // ── Voice: event-style (direction change only; home_screen adds heading gates) ─
  void _onNavigationStateChanged(NavigationState s) {
    final key = s.direction.name;
    if (key == _lastSpokenKey || s.direction == NavDirection.none) return;
    _lastSpokenKey = key;

    final msg = switch (s.direction) {
      NavDirection.left    => 'Turn left',
      NavDirection.right   => 'Turn right',
      NavDirection.forward => 'Go straight',
      NavDirection.none    => '',
    };

    if (msg.isNotEmpty) {
      print('🔊 Spoke: $msg');
      _tts.speak(msg);
    }
  }

  // ── Heading Picker Widget — Demo control ───────────────────────────────────
  /// Interactive buttons to set target heading (simulate door detection)
  /// In real app, this would be replaced with computed heading from door position
  Widget _buildHeadingPicker() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E1A).withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1A2744), width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 10,
            spreadRadius: 1,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          const Text(
            'TARGET HEADING',
            style: TextStyle(
              color: Color(0xFF4A6FA5),
              fontSize: 9,
              letterSpacing: 2,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          _headingBtn('N  (0°)',   0),
          _headingBtn('NE (45°)',  45),
          _headingBtn('E  (90°)',  90),
          _headingBtn('SE (135°)', 135),
          _headingBtn('S (180°)',  180),
          _headingBtn('SW (225°)', 225),
          _headingBtn('W (270°)',  270),
          _headingBtn('NW (315°)', 315),
        ],
      ),
    );
  }

  Widget _headingBtn(String label, double deg) {
    final active = _targetHeading == deg;
    return GestureDetector(
      onTap: () {
        setState(() => _targetHeading = deg);
        print('🧭 Target heading set to: $deg°');
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: active
              ? const Color(0xFF00D4FF).withOpacity(0.2)
              : const Color(0xFF1A2744),
          border: Border.all(
            color: active
                ? const Color(0xFF00D4FF)
                : const Color(0xFF2A4070),
            width: active ? 1.5 : 1,
          ),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? const Color(0xFF00D4FF) : const Color(0xFF4A6FA5),
            fontSize: 12,
            fontWeight: FontWeight.w600,
            fontFamily: 'monospace',
          ),
        ),
      ),
    );
  }

  // ── System Info Display ────────────────────────────────────────────────────
  Widget _buildSystemInfo() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0E1A).withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1A2744), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: const [
          Text(
            'SENSOR FUSION',
            style: TextStyle(
              color: Color(0xFF00D4FF),
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 2,
            ),
          ),
          SizedBox(height: 8),
          Text(
            '🧲 Magnetometer',
            style: TextStyle(
              color: Color(0xFF4A6FA5),
              fontSize: 10,
            ),
          ),
          Text(
            '📱 Accelerometer',
            style: TextStyle(
              color: Color(0xFF4A6FA5),
              fontSize: 10,
            ),
          ),
          Text(
            '🔄 Gyroscope',
            style: TextStyle(
              color: Color(0xFF4A6FA5),
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// INTEGRATION GUIDE
// ─────────────────────────────────────────────────────────────────────────────
//
// 1. Import the HUD into your main camera/navigation screen:
//    import 'widgets/sensor_navigation_hud.dart';
//
// 2. Wrap your camera preview with the HUD:
//    Stack(
//      children: [
//        CameraPreview(controller),  // Your camera
//        SensorNavigationHUD(
//          targetHeading: computedHeadingToDoor,
//          onNavigationStateChanged: (s) => tts.speak(directionLabel(s.direction)),
//        ),
//      ],
//    )
//
// 3. Set target heading from door detection:
//    if (doorDetected) {
//      double heading = atan2(door.x - center.x, door.y - center.y) * 180 / pi;
//      setState(() => _targetHeading = heading);
//    }
//
// 4. Optional: Calibrate compass when standing at door:
//    _sensorNav.calibrate();  // User stands facing through door, taps button
//
// ─────────────────────────────────────────────────────────────────────────────
// VOICE COMMANDS
// ─────────────────────────────────────────────────────────────────────────────
//
// The HUD emits NavigationState updates to onNavigationStateChanged()
// Use this to trigger TTS:
//
//   void _onNavigationStateChanged(NavigationState s) {
//     switch (s.direction) {
//       case NavDirection.left:
//         _tts.speak('Turn left');
//       case NavDirection.right:
//         _tts.speak('Turn right');
//       case NavDirection.forward:
//         _tts.speak('Go straight');
//       case NavDirection.none:
//         break;
//     }
//   }
//
// ─────────────────────────────────────────────────────────────────────────────
// SENSOR ACCURACY TIPS
// ─────────────────────────────────────────────────────────────────────────────
//
// 1. Calibration: Call SensorNavigationService.calibrate() when user stands
//    at door facing the direction they should walk
//
// 2. Confidence: HUD shows STABLE/FAIR/UNSTABLE based on phone tilt
//    - Keep phone vertical (portrait) for best accuracy
//    - Avoid holding phone flat (landscape)
//
// 3. Magnetic interference: Compass is affected by:
//    - Metal objects nearby
//    - Electronics (phones, laptops)
//    - Building metal reinforcement
//    - Solution: Move away from interference, recalibrate
//
// 4. Update rate: Sensors update ~20-100 times per second
//    Automatic smoothing with circular buffer of 8 readings
//
// ─────────────────────────────────────────────────────────────────────────────
// TESTING ON DEVICE
// ─────────────────────────────────────────────────────────────────────────────
//
// 1. Run app on device:
//    flutter run
//
// 2. See the HUD at bottom with live compass
//
// 3. Tap heading buttons (N/NE/E/SE/S/SW/W/NW) to set target
//
// 4. Watch the arrow change direction as you point phone in different directions
//
// 5. Listen for voice commands when direction changes
//
// ─────────────────────────────────────────────────────────────────────────────
