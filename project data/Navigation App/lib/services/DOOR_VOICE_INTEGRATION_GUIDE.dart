/// ═══════════════════════════════════════════════════════════════════════════
/// DOOR VOICE COMMAND SERVICE — INTEGRATION GUIDE
/// ═══════════════════════════════════════════════════════════════════════════
///
/// This file provides step-by-step integration instructions for the
/// DoorVoiceCommandService in your HomeScreen.
///
/// The DoorVoiceCommandService ensures voice guidance is spoken ONLY ONCE
/// per unique door + direction combination, preventing repetitive announcements.
///
/// ═══════════════════════════════════════════════════════════════════════════

// STEP 1: ADD IMPORT AT TOP OF home_screen.dart
// ───────────────────────────────────────────────────────────────────────────
// Add this line to the imports section:
//
//    import '../services/door_voice_command_service.dart';
//
// ═══════════════════════════════════════════════════════════════════════════

// STEP 2: ADD SERVICE INSTANCE IN _HomeScreenState CLASS
// ───────────────────────────────────────────────────────────────────────────
// In the _HomeScreenState class, add this field alongside other services:
//
//    final DetectionService _detectionService = DetectionService();
//    final VoiceService _voiceService = VoiceService();
//    late DoorVoiceCommandService _doorVoiceCmd;  // ← ADD THIS LINE
//
// ═══════════════════════════════════════════════════════════════════════════

// STEP 3: INITIALIZE SERVICE IN initState()
// ───────────────────────────────────────────────────────────────────────────
// In the initState() method, add initialization after VoiceService creation:
//
//    @override
//    void initState() {
//      super.initState();
//      WidgetsBinding.instance.addObserver(this);
//      _initializeCamera();
//      _checkBackendHealth();
//      
//      // Initialize door voice command service
//      _doorVoiceCmd = DoorVoiceCommandService(_voiceService);
//    }
//
// ═══════════════════════════════════════════════════════════════════════════

// STEP 4: INTEGRATE INTO DETECTION CALLBACK
// ───────────────────────────────────────────────────────────────────────────
// Find the section where you process detection responses (around line 280-300).
// 
// REPLACE the door detection voice section with this:
//
//    if (response.detections.isNotEmpty) {
//      // Find door detection
//      final doorDetection = response.detections
//          .firstWhere((d) => d.className.toLowerCase() == 'door', 
//                      orElse: () => null as dynamic);
//      
//      if (doorDetection != null && response.navigation.direction != null) {
//        // SPEAK DOOR NAVIGATION ONCE PER DOOR+DIRECTION COMBO
//        await _doorVoiceCmd.speakOnce(
//          response.navigation.direction!,
//          doorDetection,
//        );
//      } else {
//        // No door detected - reset voice to allow next door to speak
//        _doorVoiceCmd.reset();
//      }
//    } else {
//      // No detections at all
//      _doorVoiceCmd.reset();
//    }
//
// ═══════════════════════════════════════════════════════════════════════════

// STEP 5: UPDATE dispose() METHOD
// ───────────────────────────────────────────────────────────────────────────
// Add cleanup for the door voice service in dispose():
//
//    @override
//    void dispose() {
//      WidgetsBinding.instance.removeObserver(this);
//      _detectionTimer?.cancel();
//      _stopCameraStream();
//      _cameraController?.dispose();
//      _voiceService.stop();
//      _doorVoiceCmd.clearAllHistory();  // ← ADD THIS LINE
//      super.dispose();
//    }
//
// ═══════════════════════════════════════════════════════════════════════════

// COMPLETE INTEGRATION EXAMPLE
// ───────────────────────────────────────────────────────────────────────────
// Here's how your _processDetectionFrame() method should look:
//
/*
Future<void> _processDetectionFrame() async {
  if (!mounted || _cameraController == null || !_cameraController!.value.isInitialized) {
    _isProcessing = false;
    return;
  }

  _isProcessing = true;

  try {
    final image = await _cameraController?.takePicture();
    if (image != null) {
      final response = await _detectionService.detectObjects(image.path);

      if (!mounted) return;

      setState(() {
        _latestDetection = response;
      });

      // Process detection results
      if (response != null && response.detections.isNotEmpty) {
        // Find door detection if exists (avoid firstWhere+null runtime crash)
        Detection? doorDetection;
        for (final d in response.detections) {
          if (d.className.toLowerCase() == 'door') {
            doorDetection = d;
            break;
          }
        }

        // SPEAK DOOR NAVIGATION ONCE PER DOOR+DIRECTION COMBO
        if (doorDetection != null && response.navigation.direction != null) {
          await _doorVoiceCmd.speakOnce(
            response.navigation.direction!,
            doorDetection,
          );
          print('🚪 Door voice spoken: ${response.navigation.direction}');
        } else {
          // Reset when no door or direction
          _doorVoiceCmd.reset();
        }

        // Handle popup alerts (if any)
        if (response.popup.isActive) {
          print('🔊 POPUP TRIGGERED: ${response.popup.type}');
          String voiceMessage = response.popup.message;
          
          if (response.popup.type.toLowerCase() == 'door') {
            voiceMessage = 'Door detected at ${response.popup.distance.toStringAsFixed(1)} metres.';
          }
          
          await _voiceService.speak(
            voiceMessage,
            '${response.popup.type}_${response.popup.distance.toInt()}',
            cooldownSeconds: 2,
          );
        }
      } else {
        _doorVoiceCmd.reset();
      }
    }
  } catch (e) {
    print('❌ Detection error: $e');
  } finally {
    _isProcessing = false;
  }
}
*/
//
// ═══════════════════════════════════════════════════════════════════════════

// SERVICE FEATURES
// ───────────────────────────────────────────────────────────────────────────
// ✓ Speaks ONCE per unique door + direction combination
// ✓ Uses door tracking ID to prevent re-triggers for same physical door
// ✓ Automatically resets when door disappears
// ✓ Customizable voice messages for LEFT, RIGHT, FORWARD directions
// ✓ Integrates with existing VoiceService cooldown system
// ✓ Debug logging for troubleshooting
// ✓ State inspection methods for monitoring
//
// ═══════════════════════════════════════════════════════════════════════════

// VOICE MESSAGES
// ───────────────────────────────────────────────────────────────────────────
// Default messages:
//   - LEFT:    "Door detected. Move left."
//   - RIGHT:   "Door detected. Move right."
//   - FORWARD: "Door ahead. Go through."
//   - CENTER:  "Door is centered. Proceed forward."
//
// To customize messages, edit the _buildVoiceMessage() method in
// door_voice_command_service.dart
//
// ═══════════════════════════════════════════════════════════════════════════

// TROUBLESHOOTING
// ───────────────────────────────────────────────────────────────────────────
// Problem: Voice repeats multiple times
// Solution: Check that speakOnce() is being called (not speak())
//
// Problem: Voice doesn't speak when door appears
// Solution: Verify doorDetection != null and direction != null
//
// Problem: Voice doesn't reset when door disappears
// Solution: Ensure _doorVoiceCmd.reset() is called in the else block
//
// Problem: Different doors trigger same voice (poor UX)
// Solution: Verify door.trackingId is set. Check detection service output.
//
// ═══════════════════════════════════════════════════════════════════════════

// CONFIGURATION
// ───────────────────────────────────────────────────────────────────────────
// To adjust cooldown between repeated directions for same door:
// Edit the _doorVoiceCmd.speakOnce() call, change cooldownSeconds:
//
//    await _doorVoiceCmd.speakOnce(
//      response.navigation.direction!,
//      doorDetection,
//      cooldownSeconds: 5,  // ← Change this value (default: 3)
//    );
//
// ═══════════════════════════════════════════════════════════════════════════
