import 'package:flutter_tts/flutter_tts.dart';

/// Voice Guide Service for Text-to-Speech
class VoiceService {
  final FlutterTts _flutterTts = FlutterTts();
  final Map<String, DateTime> _lastSpoken = {};
  bool _isSpeaking = false;
  String? _currentSpeakingId;

  VoiceService() {
    _initTts();
  }

  /// Initialize TTS
  Future<void> _initTts() async {
    await _flutterTts.setLanguage('en-US');
    await _flutterTts.setSpeechRate(0.45); // Slightly slower for clarity
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
    
    _flutterTts.setStartHandler(() {
      _isSpeaking = true;
      print('🔊 Voice started');
    });
    
    _flutterTts.setCompletionHandler(() {
      _isSpeaking = false;
      _currentSpeakingId = null;
      print('🔊 Voice completed');
    });
    
    _flutterTts.setErrorHandler((msg) {
      print('🔊 TTS Error: $msg');
      _isSpeaking = false;
      _currentSpeakingId = null;
    });
  }

  /// Speak text with cooldown to avoid repetition
  /// For popup alerts, set isPopup=true to bypass cooldown
  Future<void> speak(
    String text,
    String objectId, {
    int cooldownSeconds = 4,
    bool isPopup = false,
  }) async {
    // For popups, skip the cooldown check
    if (!isPopup) {
      // Check cooldown for regular messages
      final now = DateTime.now();
      if (_lastSpoken.containsKey(objectId)) {
        final lastTime = _lastSpoken[objectId]!;
        if (now.difference(lastTime).inSeconds < cooldownSeconds) {
          return; // Skip if within cooldown period
        }
      }
    }
    
    // Don't queue up multiple speeches - stop current and speak new
    if (_isSpeaking && _currentSpeakingId != objectId) {
      // Only interrupt if it's a popup (higher priority)
      if (!isPopup) {
        return;
      }
      // Stop current speech for popup alerts
      await _flutterTts.stop();
      _isSpeaking = false;
    }
    
    // Update last spoken time
    _lastSpoken[objectId] = DateTime.now();
    _currentSpeakingId = objectId;
    
    // Speak with enhanced volume
    try {
      print('🔊 Speaking: $text (ID: $objectId, isPopup: $isPopup)');
      await _flutterTts.setVolume(1.0); // Max volume
      await _flutterTts.speak(text);
    } catch (e) {
      print('🔊 Speak error: $e');
      _isSpeaking = false;
      _currentSpeakingId = null;
    }
  }

  /// Speak with immediate priority (for emergency alerts)
  Future<void> speakUrgent(String text, String objectId) async {
    // Stop any current speech
    if (_isSpeaking) {
      await _flutterTts.stop();
    }
    
    // Update cooldown and speak
    _lastSpoken[objectId] = DateTime.now();
    _currentSpeakingId = objectId;
    
    try {
      print('🔊 URGENT: $text (ID: $objectId)');
      await _flutterTts.setVolume(1.0);
      await _flutterTts.speak(text);
    } catch (e) {
      print('🔊 Urgent speak error: $e');
      _isSpeaking = false;
      _currentSpeakingId = null;
    }
  }

  /// Stop speaking
  Future<void> stop() async {
    await _flutterTts.stop();
    _isSpeaking = false;
    _currentSpeakingId = null;
  }

  /// Dispose resources
  void dispose() {
    _flutterTts.stop();
  }

  /// Check if currently speaking
  bool get isSpeaking => _isSpeaking;
}
