import 'package:navigation_app/models/detection_model.dart';
import 'voice_service.dart';

/// Door Voice Command Service (SIMPLIFIED - NO LOOPING)
///
/// Speaks navigation direction ONLY ONCE when door is first detected.
/// After that, stays silent until door completely disappears and is
/// reset. No repeated voice messages while door stays visible.
class DoorVoiceCommandService {
  final VoiceService _voiceService;

  // Track if we've already spoken for the current door
  String? _lastSpokenDoorKey;

  // How many frames door must be absent before we can reset
  static const int _absenceThreshold = 10;
  int _absentFrameCount = 0;

  // Grid size for position snapping to avoid jitter
  static const int _gridSize = 80;

  DoorVoiceCommandService(this._voiceService);

  /// Get door position hash (snapped to grid for stability)
  String _getDoorPositionHash(Detection door) {
    // Snap to grid to ignore small jitter
    final gx = (door.position.centerX / _gridSize).round();
    final gy = (door.position.centerY / _gridSize).round();
    final gd = (door.distance / 50).round();
    return '${gx}_${gy}_${gd}';
  }

  /// Call every frame when door IS detected.
  /// Speaks only ONCE. After that, silent until door completely gone.
  /// NO LOOPING - voice triggers only on first detection.
  Future<void> speakOnce(String direction, Detection door) async {
    // Reset absence counter — door is here right now
    _absentFrameCount = 0;

    final doorKey = _getDoorPositionHash(door);

    // Already spoke for this door? → Stay silent (NO LOOPING)
    if (_lastSpokenDoorKey == doorKey) {
      return; // Silent — no voice repetition
    }

    // New door detected → Speak once
    _lastSpokenDoorKey = doorKey;

    final message = _buildVoiceMessage(direction);
    await _voiceService.speak(
      message,
      'door_$doorKey',
      cooldownSeconds: 1,
      isPopup: false,
    );

    print('🚪 Door detected (voice once): $message');
  }

  /// Call every frame when NO door detected.
  /// Only resets after threshold to avoid flickering.
  void markAbsent() {
    _absentFrameCount++;
    if (_absentFrameCount >= _absenceThreshold) {
      if (_lastSpokenDoorKey != null) {
        print('🚪 Door gone → ready for next door');
      }
      _lastSpokenDoorKey = null;
      _absentFrameCount = 0;
    }
  }

  /// Hard reset for new navigation session
  void clearAllHistory() {
    _lastSpokenDoorKey = null;
    _absentFrameCount = 0;
    print('🚪 Door voice session cleared');
  }

  String _buildVoiceMessage(String direction) {
    switch (direction.toUpperCase()) {
      case 'LEFT':
        return 'Door detected. Move left.';
      case 'RIGHT':
        return 'Door detected. Move right.';
      case 'FORWARD':
        return 'Door ahead. Go forward.';
      case 'CENTER':
        return 'Door is centered.';
      default:
        return 'Door detected.';
    }
  }

  String get currentState => _lastSpokenDoorKey ?? 'idle';
}

