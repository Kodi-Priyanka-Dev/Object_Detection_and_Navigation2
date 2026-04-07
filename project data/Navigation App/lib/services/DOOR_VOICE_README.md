═══════════════════════════════════════════════════════════════════════════
  DOOR VOICE COMMAND SERVICE - QUICK REFERENCE
═══════════════════════════════════════════════════════════════════════════

✅ WHAT'S BEEN DONE:

1. ✓ Created: lib/services/door_voice_command_service.dart
   - Handles "speak once per door detection" logic
   - Uses door tracking ID to prevent re-triggers
   - Automatically resets when door disappears

2. ✓ Created: lib/services/DOOR_VOICE_INTEGRATION_GUIDE.dart
   - Complete step-by-step integration instructions
   - Code examples and troubleshooting
   - Configuration options

3. ✓ Updated: lib/screens/home_screen.dart
   - ✓ Added import for door_voice_command_service
   - ✓ Added _doorVoiceCmd service instance
   - ✓ Initialized in initState()
   - ✓ Integrated in detection callback
   - ✓ Added cleanup in dispose()

═══════════════════════════════════════════════════════════════════════════

📋 HOW IT WORKS:

When a door is detected + direction is available:
  1. DoorVoiceCommandService.speakOnce() is called
  2. Checks if this exact door+direction combo was already spoken
  3. If NEW: Speaks the voice message once
  4. If SAME: Skips (no repetition)
  
When door disappears or no direction:
  1. _doorVoiceCmd.reset() is called
  2. Clears the tracking - next door will speak

═══════════════════════════════════════════════════════════════════════════

🎤 VOICE MESSAGES:

LEFT:    "Door detected. Move left."
RIGHT:   "Door detected. Move right."
FORWARD: "Door ahead. Go through."
CENTER:  "Door is centered. Proceed forward."

═══════════════════════════════════════════════════════════════════════════

🚀 TO BUILD AND DEPLOY:

1. Run: flutter pub get
2. Run: flutter run -d <device_id>
   
   Or via ADB to Vivo device:
   adb connect 10.26.67.141:5555
   flutter run

═══════════════════════════════════════════════════════════════════════════

🔧 FEATURES:

✓ Speaks ONCE per unique door + direction combo
✓ Uses door tracking ID to identify same physical door
✓ Auto-resets when door disappears
✓ Integrated cooldown system (3 seconds default)
✓ Debug logging for troubleshooting
✓ State inspection methods
✓ Works with existing NavigationArrow widget distance fade

═══════════════════════════════════════════════════════════════════════════

⚡ KEY FILES:

1. door_voice_command_service.dart
   - Location: lib/services/
   - Purpose: Voice command logic
   - Public methods:
     * speakOnce(direction, door)
     * reset()
     * clearAllHistory()
     * currentState (getter)
     * wasRecentlySpoken(direction, door)

2. home_screen.dart (UPDATED)
   - Added DoorVoiceCommandService instance
   - Integrated in detection callback
   - Proper initialization & cleanup

═══════════════════════════════════════════════════════════════════════════

📊 INTEGRATION POINTS IN home_screen.dart:

Line ~6:     import door_voice_command_service.dart
Line ~28:    late DoorVoiceCommandService _doorVoiceCmd;
Line ~40:    _doorVoiceCmd = DoorVoiceCommandService(_voiceService);
Line ~65:    _doorVoiceCmd.clearAllHistory();
Line ~305:   await _doorVoiceCmd.speakOnce(...);
Line ~350:   _doorVoiceCmd.reset();

═══════════════════════════════════════════════════════════════════════════

💡 TESTING:

1. Open Flutter app on device
2. Point camera at a door
3. Listen for voice: "Door detected. Move [direction]."
4. Move closer to door
5. Voice stops repeating (correct behavior)
6. Move to different door
7. Hear voice again for new door (correct behavior)

═══════════════════════════════════════════════════════════════════════════

🔍 TROUBLESHOOTING:

Issue: Voice repeats multiple times
→ Ensure speakOnce() is being called (not speak())
→ Check door.trackingId is properly set

Issue: Voice doesn't speak
→ Verify door detection exists (className == 'door')
→ Check response.navigation.direction is not null
→ Check VoiceService is initialized
→ Check app permissions for audio

Issue: Voice doesn't reset
→ Verify _doorVoiceCmd.reset() is called in else blocks
→ Check detection response is null or empty

═══════════════════════════════════════════════════════════════════════════

🎛️ CUSTOMIZATION:

To change voice messages → Edit _buildVoiceMessage() in door_voice_command_service.dart
To change cooldown → Edit cooldownSeconds parameter in speakOnce() call
To change distance threshold → Edit distanceThreshold in NavigationArrow

═══════════════════════════════════════════════════════════════════════════

📱 DEVICE INFO:

Target: Vivo V2303
Backend: Flask on 10.26.67.141:5000
Model: detect1892 (88.87% mAP@0.5)
Classes: 20 (including Door class)

═══════════════════════════════════════════════════════════════════════════

✅ INTEGRATION COMPLETE!

The system is ready. Build and test on your device:

  flutter run -d <device_id>

═══════════════════════════════════════════════════════════════════════════
