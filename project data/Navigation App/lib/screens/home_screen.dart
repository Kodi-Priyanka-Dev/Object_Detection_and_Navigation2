import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'dart:async';
import 'dart:math';
import '../services/detection_service.dart';
import '../services/voice_service.dart';
import '../services/door_voice_command_service.dart';
import '../services/sensor_navigation_service.dart';
import '../models/detection_model.dart';
import '../widgets/object_labels.dart';
import '../widgets/navigation_arrow.dart';
import '../widgets/navigation_popup.dart';
import '../widgets/door_popup_dialog.dart';
import '../widgets/door_arrow_overlay.dart';
import '../widgets/sensor_navigation_hud.dart';
import '../widgets/door_detection_alert.dart';
import 'debug_visualization_screen.dart';

/// Tuning for door arrow: same-door tracking + EMA distance + jump limit.
class DoorTrackingTuning {
  static const int maxDoorMissingFrames = 10;
  static const double doorEmaAlphaDist = 0.28;
  static const double maxDistanceStepPerFrameM = 0.65;
  static const double doorEmaAlphaPos = 0.35;
  static const double trackMatchGateNorm = 0.18;
  static const double fastAlphaOnLargeAreaChange = 0.45;
  static const double areaChangeTrigger = 0.22;
}

class HomeScreen extends StatefulWidget {
  final List<CameraDescription> cameras;

  const HomeScreen({Key? key, required this.cameras}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  CameraController? _cameraController;
  final DetectionService _detectionService = DetectionService();
  final VoiceService _voiceService = VoiceService();
  late DoorVoiceCommandService _doorVoiceCmd;
  
  bool _isProcessing = false;
  bool _isBackendHealthy = false;
  String _currentModel = 'custom'; // Track current model
  bool _isSwitchingModel = false; // Prevent multiple concurrent switches
  DetectionResponse? _latestDetection;
  Timer? _detectionTimer;
  int _frameSkipCounter = 0;
  static const int FRAME_SKIP = 2; // Process every 2nd frame (~15 FPS) for balanced latency
  bool _isDoorDialogOpen = false;
  String? _shownPopupDoorKey = null; // Track if popup already shown for this door (NO LOOPING)

  // Door tracker: same door across frames; smoothed distance/position for arrow UI.
  Detection? _trackedDoorDetection;
  double? _smoothedDoorDistanceM;
  double? _smoothedDoorXNorm;
  double? _smoothedDoorYNorm;
  double? _smoothedDoorAreaNorm;
  int _doorMissingFrames = 0;

  // Event-based sensor voice: heading/tilt change + cooldown (reduces repetition).
  DateTime? _lastSensorGuidanceVoiceAt;
  double? _lastSensorVoiceHeading;
  double? _lastSensorVoiceTilt;
  NavDirection? _lastSensorVoiceDir;

  static const int _maxDoorMissingFrames = DoorTrackingTuning.maxDoorMissingFrames;
  static const double _doorEmaAlphaDist = DoorTrackingTuning.doorEmaAlphaDist;
  static const double _doorEmaAlphaPos = DoorTrackingTuning.doorEmaAlphaPos;
  static const double _maxDistanceStepPerFrameM = DoorTrackingTuning.maxDistanceStepPerFrameM;
  static const double _trackMatchGateNorm = DoorTrackingTuning.trackMatchGateNorm;
  static const double _fastAlphaOnLargeAreaChange = DoorTrackingTuning.fastAlphaOnLargeAreaChange;
  static const double _areaChangeTrigger = DoorTrackingTuning.areaChangeTrigger;

  /// Pick the door that best continues the current track (spatial + area), else nearest.
  Detection _selectTrackedDoorCandidate(
    List<Detection> doorCandidates,
    double frameW,
    double frameH,
  ) {
    if (_smoothedDoorXNorm == null ||
        _smoothedDoorYNorm == null ||
        _smoothedDoorAreaNorm == null) {
      doorCandidates.sort((a, b) => a.distance.compareTo(b.distance));
      return doorCandidates.first;
    }

    Detection best = doorCandidates.first;
    double bestScore = double.infinity;

    for (final d in doorCandidates) {
      final xNorm = (d.position.centerX / frameW).clamp(0.0, 1.0);
      final yNorm = (d.position.centerY / frameH).clamp(0.0, 1.0);
      final areaNorm =
          ((d.width.toDouble() * d.height.toDouble()) / (frameW * frameH))
              .clamp(0.0, 1.0);

      final dx = xNorm - _smoothedDoorXNorm!;
      final dy = yNorm - _smoothedDoorYNorm!;
      final posDelta = sqrt(dx * dx + dy * dy);
      final areaDelta = (areaNorm - _smoothedDoorAreaNorm!).abs();

      final score =
          (posDelta * 2.2) + (areaDelta * 0.7) - (d.confidence * 0.15);
      if (score < bestScore) {
        bestScore = score;
        best = d;
      }
    }

    if (bestScore > _trackMatchGateNorm) {
      doorCandidates.sort((a, b) => a.distance.compareTo(b.distance));
      return doorCandidates.first;
    }

    return best;
  }

  double _circularDiffDegrees(double a, double b) {
    var d = (a - b).abs() % 360.0;
    if (d > 180.0) d = 360.0 - d;
    return d;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
    _checkBackendHealth();
    
    // Initialize door voice command service
    _doorVoiceCmd = DoorVoiceCommandService(_voiceService);
  }

  @override
  void dispose() {
    // Remove lifecycle observer
    WidgetsBinding.instance.removeObserver(this);
    
    // Stop detection timer
    _detectionTimer?.cancel();
    
    // Stop camera stream FIRST (critical - prevent JNI access after detach)
    _stopCameraStream();
    
    // Dispose camera controller
    try {
      _cameraController?.dispose();
    } catch (e) {
      print('Error disposing camera: $e');
    }
    _cameraController = null;
    
    // Stop voice service
    try {
      _voiceService.stop();
    } catch (e) {
      print('Error stopping voice: $e');
    }
    
    // Clear door voice command history
    try {
      _doorVoiceCmd.clearAllHistory();
    } catch (e) {
      print('Error clearing door voice history: $e');
    }
    
    super.dispose();
  }
  
  /// Safely stop camera stream with proper state checks
  void _stopCameraStream() {
    if (!mounted) return;
    try {
      _cameraController?.stopImageStream();
      _isProcessing = false;
    } catch (e) {
      // Ignore errors when stream already stopped
      if (!e.toString().contains('already stopped')) {
        print('Error stopping camera stream: $e');
      }
    }
  }

  // Handle app lifecycle changes
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!mounted) return;

    switch (state) {
      case AppLifecycleState.paused:
        // App is paused - stop processing frames and cancel all timers
        print('🛑 App paused - stopping camera stream');
        _detectionTimer?.cancel();
        _stopCameraStream();
        try {
          _voiceService.stop();
        } catch (e) {
          print('Error stopping voice on pause: $e');
        }
        break;

      case AppLifecycleState.resumed:
        // App is resumed - restart camera stream
        print('▶️  App resumed - restarting camera stream');
        if (_cameraController != null && _cameraController!.value.isInitialized && mounted) {
          try {
            _startDetectionStream();
            _checkBackendHealth();
          } catch (e) {
            print('Error resuming camera stream: $e');
          }
        }
        break;

      case AppLifecycleState.detached:
        // App is detached - critical: stop all frame processing
        print('⏹️  App detached - emergency shutdown');
        _detectionTimer?.cancel();
        _stopCameraStream();
        break;

      case AppLifecycleState.hidden:
        // App is hidden (rarely used)
        break;

      case AppLifecycleState.inactive:
        // App is inactive
        break;
    }
  }

  /// Initialize camera
  Future<void> _initializeCamera() async {
    if (widget.cameras.isEmpty) {
      print('No cameras available');
      return;
    }

    _cameraController = CameraController(
      widget.cameras[0],
      ResolutionPreset.ultraHigh,  // Improved: Changed from 'high' to 'ultraHigh'
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,  // Improved: Specify JPEG format for better compression
    );

    try {
      await _cameraController!.initialize();
      
      // Improve camera settings for better quality
      try {
        await _cameraController!.setFlashMode(FlashMode.off);  // Disable flash for consistent indoor detection
        await _cameraController!.setExposureMode(ExposureMode.auto);  // Auto exposure
        await _cameraController!.setFocusMode(FocusMode.auto);  // Auto focus
      } catch (e) {
        print('Warning: Could not set camera settings: $e');
      }
      
      if (mounted) {
        setState(() {});
        _startDetectionStream();
      }
    } catch (e) {
      print('Camera initialization error: $e');
    }
  }

  /// Check backend health
  Future<void> _checkBackendHealth() async {
    final healthData = await _detectionService.healthCheck();
    if (mounted && healthData != null) {
      setState(() {
        _isBackendHealthy = healthData['status'] == 'healthy';
        _currentModel = healthData['current_model'] ?? 'custom';
      });
      print('✓ Backend: ${_isBackendHealthy ? "healthy" : "offline"} | Model: $_currentModel');
    }
  }

  /// Switch between models
  Future<void> _switchModel(String modelName) async {
    if (_isSwitchingModel) return; // Prevent concurrent switches
    
    setState(() {
      _isSwitchingModel = true;
    });
    
    final success = await _detectionService.switchModel(modelName);
    
    if (mounted) {
      setState(() {
        if (success) {
          _currentModel = modelName;
        }
        _isSwitchingModel = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            success 
              ? '✅ Switched to $modelName'
              : '❌ Failed to switch model',
          ),
          duration: const Duration(seconds: 2),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  /// Start detection stream
  void _startDetectionStream() {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    // Start image stream directly - this is more efficient than polling
    try {
      _cameraController!.startImageStream((CameraImage image) {
        // Skip frames to reduce backend load
        _frameSkipCounter++;
        if (_frameSkipCounter < FRAME_SKIP) {
          return;
        }
        _frameSkipCounter = 0;

        // Process this frame
        _onImageAvailable(image);
      });
    } catch (e) {
      print('Error starting image stream: $e');
    }
  }

  /// Handle camera image stream
  void _onImageAvailable(CameraImage cameraImage) async {
    // Don't process if widget is not mounted or already processing
    if (!mounted || _isProcessing) return;
    
    if (mounted) {
      setState(() {
        _isProcessing = true;
      });
    }

    try {
      // Send to backend for detection
      final rotation = _cameraController?.description.sensorOrientation ?? 0;
      final response = await _detectionService.detectObjects(
        cameraImage,
        rotationDegrees: rotation,
      );
      
      if (response != null && mounted) {
        print('📊 Detection response: ${response.detections.length} objects detected');
        print('📍 Navigation popup: ${response.navigation.popup?.type ?? "none"}');
        
        setState(() {
          _latestDetection = response;

          // Door tracker: same-door association + jump-limited EMA on distance;
          // EMA on screen position so arrow and distance stay aligned.
          final frameW = response.frameSize.width.toDouble();
          final frameH = response.frameSize.height.toDouble();
          final doorCandidates = response.detections
              .where((d) => d.className.toLowerCase().contains('door'))
              .toList();

          if (doorCandidates.isNotEmpty && frameW > 0 && frameH > 0) {
            final door = _selectTrackedDoorCandidate(doorCandidates, frameW, frameH);

            _trackedDoorDetection = door;
            _doorMissingFrames = 0;

            final rawDist = door.distance;
            final doorAreaNorm =
                ((door.width.toDouble() * door.height.toDouble()) / (frameW * frameH))
                    .clamp(0.0, 1.0);

            if (_smoothedDoorDistanceM == null) {
              _smoothedDoorDistanceM = rawDist;
            } else {
              final prev = _smoothedDoorDistanceM!;
              final areaDelta = _smoothedDoorAreaNorm == null
                  ? 0.0
                  : (doorAreaNorm - _smoothedDoorAreaNorm!).abs();

              final adaptiveAlpha = areaDelta > _areaChangeTrigger
                  ? _fastAlphaOnLargeAreaChange
                  : _doorEmaAlphaDist;
              final adaptiveStep = areaDelta > _areaChangeTrigger
                  ? _maxDistanceStepPerFrameM * 1.8
                  : _maxDistanceStepPerFrameM;

              final clampedRaw = rawDist.clamp(
                prev - adaptiveStep,
                prev + adaptiveStep,
              );
              _smoothedDoorDistanceM =
                  adaptiveAlpha * clampedRaw + (1 - adaptiveAlpha) * prev;
            }

            final xNorm = (door.position.centerX / frameW).clamp(0.0, 1.0);
            final yNorm = (door.position.centerY / frameH).clamp(0.0, 1.0);

            _smoothedDoorXNorm = _smoothedDoorXNorm == null
                ? xNorm
                : (_doorEmaAlphaPos * xNorm +
                    (1 - _doorEmaAlphaPos) * _smoothedDoorXNorm!);
            _smoothedDoorYNorm = _smoothedDoorYNorm == null
                ? yNorm
                : (_doorEmaAlphaPos * yNorm +
                    (1 - _doorEmaAlphaPos) * _smoothedDoorYNorm!);
            _smoothedDoorAreaNorm = _smoothedDoorAreaNorm == null
                ? doorAreaNorm
                : (0.25 * doorAreaNorm + 0.75 * _smoothedDoorAreaNorm!);
          } else {
            _doorMissingFrames++;
            if (_doorMissingFrames > _maxDoorMissingFrames) {
              _trackedDoorDetection = null;
              _smoothedDoorDistanceM = null;
              _smoothedDoorXNorm = null;
              _smoothedDoorYNorm = null;
              _smoothedDoorAreaNorm = null;
              // Reset popup + voice history so the next re-detected door
              // triggers a fresh popup + voice message.
              _shownPopupDoorKey = null;
              _doorVoiceCmd.clearAllHistory();
            }
          }

        });

        // Handle voice guidance - prioritize popups
        if (response.navigation.popup != null) {
          final popup = response.navigation.popup!;

          // Show blocking door decision popup and send response to backend.
          // BUT: Only show popup ONCE per door (NO LOOPING)
          if (popup.type.toLowerCase() == 'door' && !_isDoorDialogOpen) {
            
            // Create a key for this door detection (spatial position only, not distance)
            Detection? doorDetection;
            try {
              doorDetection = response.detections.firstWhere(
                (d) => d.className.toLowerCase().contains('door'),
              );
            } catch (e) {
              // No door detection found in list, door detection likely from position only
              doorDetection = null;
            }
            
            String? doorKey = null;
            if (doorDetection != null) {
              // Snap to 150px grid to ignore jitter (larger grid = fewer duplicate popups)
              // Use only X,Y position - ignore distance to prevent fluctuation-based duplicates
              final gx = (doorDetection.position.centerX / 150).round();
              final gy = (doorDetection.position.centerY / 150).round();
              doorKey = '${gx}_${gy}';
            }
            
            if (doorKey != null && doorKey != _shownPopupDoorKey) {
              _isDoorDialogOpen = true;
              _shownPopupDoorKey = doorKey;

              final double doorDistanceForUi = _smoothedDoorDistanceM ??
                  doorDetection?.distance ??
                  popup.distance;

              final doorVoiceMessage =
                  'Door is detected at ${doorDistanceForUi.toStringAsFixed(1)} meters. Do you want to open and go?';

              // Fire-and-forget so the popup appears immediately.
              // Use isPopup=true to bypass cooldown and allow interruption.
              _voiceService.speak(
                doorVoiceMessage,
                'door_popup_$doorKey',
                cooldownSeconds: 0,
                isPopup: true,
              );
              
              final bool? userChoice = await DoorPopupDialog.showDoorPopup(
                context,
                doorDistanceForUi,
              );

              final doorClass = doorDetection?.className ?? 'Door';

              await _detectionService.handleDoorResponse(
                userResponse: userChoice == true ? 'yes' : 'no',
                doorClass: doorClass,
                doorDistance: doorDistanceForUi,
              );
              _isDoorDialogOpen = false;
            }
          }

          print('🔊 POPUP (NO LOOP): ${popup.type} at ${popup.distance}m');
          // Door voice is already spoken when the dialog is shown above.
          if (popup.type.toLowerCase() != 'door') {
            String voiceMessage = popup.message;
            if (popup.type.toLowerCase() == 'human') {
              voiceMessage = 'Human detected. Deviate and go straight.';
            }

            print('📢 Speaking: $voiceMessage');
            await _voiceService.speak(
              voiceMessage,
              '${popup.type}_${popup.distance.toInt()}',
              cooldownSeconds: 2,
            );
          }
        } else if (response.navigation.direction != null && 
                   response.detections.isNotEmpty) {
          // ────────────────────────────────────────────────────────────────
          // DOOR VOICE COMMAND - Speak once per unique door + direction combo
          // ────────────────────────────────────────────────────────────────
          // Find door detection if exists (do not use firstWhere+null; it crashes at runtime)
          Detection? doorDetection;
          for (final d in response.detections) {
            if (d.className.toLowerCase().contains('door')) {
              doorDetection = d;
              break;
            }
          }

          if (doorDetection != null) {
            await _doorVoiceCmd.speakOnce(
              response.navigation.direction!,
              doorDetection,
            );
            print('🚪 Door voice: ${response.navigation.direction}');
          } else {
            if (response.navigation.message != null) {
              print('📣 Navigation guidance: ${response.navigation.message}');
              await _voiceService.speak(
                response.navigation.message!,
                'nav_${response.navigation.direction}',
                cooldownSeconds: 4,
              );
            }
          }
        } else if (response.navigation.message != null) {
          print('📣 Navigation guidance: ${response.navigation.message}');
          await _voiceService.speak(
            response.navigation.message!,
            'nav_${response.navigation.direction}',
            cooldownSeconds: 4,
          );
        } else if (response.detections.isNotEmpty) {
          // Reset door voice when detections exist but no direction
          _doorVoiceCmd.clearAllHistory();
          _shownPopupDoorKey = null; // Reset popup tracking too
          
          // Log detected objects even without popup/message
          final objectNames = response.detections
              .map((d) => '${d.className} (${d.confidence})')
              .join(', ');
          print('🎯 Detected objects: $objectNames');
        }
      } else if (response == null) {
        _doorVoiceCmd.clearAllHistory();
        _shownPopupDoorKey = null;
        if (mounted) {
          setState(() {
            _lastSensorGuidanceVoiceAt = null;
            _lastSensorVoiceHeading = null;
            _lastSensorVoiceTilt = null;
            _lastSensorVoiceDir = null;
          });
        }
        print('❌ Detection service returned null');
      } else if (response.detections.isEmpty) {
        // Reset when no detections
        _doorVoiceCmd.clearAllHistory();
        _shownPopupDoorKey = null; // Reset popup tracking - allow new popups
        print('❌ No detections found');
      }
    } catch (e) {
      print('❌ Detection error: $e');
    } finally {
      // Always stop processing flag, with mounted check
      try {
        if (mounted) {
          setState(() {
            _isProcessing = false;
          });
        } else {
          _isProcessing = false;
        }
      } catch (e) {
        // Ignore setState errors if widget is unmounted
        _isProcessing = false;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            // Camera Preview
            _buildCameraPreview(),
            
            // Object Labels (NO bounding boxes)
            if (_latestDetection != null && 
                _latestDetection!.frameSize.width > 0 &&
                _latestDetection!.frameSize.height > 0)
              ObjectLabels(
                detections: _latestDetection!.detections,
                screenSize: Size(
                  _latestDetection!.frameSize.width.toDouble(),
                  _latestDetection!.frameSize.height.toDouble(),
                ),
              ),
            
            // Door direction arrow (tracked door + smoothed position/distance)
            if (_trackedDoorDetection != null &&
                _smoothedDoorDistanceM != null &&
                _smoothedDoorXNorm != null &&
                _smoothedDoorYNorm != null)
              _buildDoorArrowOverlay(),
            
            
            // Door Detection Alert (below status bar)
            if (_latestDetection != null && _latestDetection!.detections.isNotEmpty)
              DoorDetectionAlert(
                detection: _latestDetection!,
              ),
            
            _buildHumanNavigationPopup(),
            
            // Status indicators (top)
            _buildStatusBar(),
            
            // Control Panel (bottom)
            _buildControlPanel(),
            
            // Sensor Navigation HUD with compass and direction guidance
            Positioned(
              left: 10,
              right: 10,
              bottom: _sensorPanelBottomOffset(context),
              child: SensorNavigationHUD(
                showGuidance: true,
                onNavigationStateChanged: _onSensorNavigationStateChanged,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Human / obstacle navigation card (door uses modal dialog instead).
  Widget _buildHumanNavigationPopup() {
    final pop = _latestDetection?.navigation.popup;
    if (pop == null || pop.type.toLowerCase() == 'door') {
      return const SizedBox.shrink();
    }
    return Positioned(
      top: 120,
      left: 10,
      right: 10,
      child: Transform.scale(
        scale: 0.82,
        alignment: Alignment.topCenter,
        child: NavigationPopupWidget(
          popup: pop,
        ),
      ),
    );
  }

  /// Build door arrow overlay with distance
  Widget _buildDoorArrowOverlay() {
    if (_trackedDoorDetection == null ||
        _smoothedDoorDistanceM == null ||
        _smoothedDoorXNorm == null ||
        _smoothedDoorYNorm == null) {
      return const SizedBox.shrink();
    }

    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;
    if (screenWidth <= 0 || screenHeight <= 0) {
      return const SizedBox.shrink();
    }

    final xPos = _smoothedDoorXNorm! * screenWidth;
    final yPos = _smoothedDoorYNorm! * screenHeight;
    if (!xPos.isFinite || !yPos.isFinite) {
      return const SizedBox.shrink();
    }

    return DoorArrowOverlay(
      position: Offset(xPos, yPos),
      screenSize: Size(screenWidth, screenHeight),
      distance: _smoothedDoorDistanceM!,
    );
  }

  /// Build navigation arrow positioned near door if detected
  Widget _buildNavigationArrow() {
    // Find door in detections
    Detection? doorDetection;
    if (_latestDetection != null) {
      try {
        doorDetection = _latestDetection!.detections.firstWhere(
          (d) => d.className.toLowerCase().contains('door'),
        );
      } catch (e) {
        // No door found
      }
    }

    if (doorDetection != null && _latestDetection != null &&
        _latestDetection!.frameSize.width > 0 &&
        _latestDetection!.frameSize.height > 0) {
      // Position arrow near the door
      final xPos = (doorDetection.position.centerX / _latestDetection!.frameSize.width) * 
                   MediaQuery.of(context).size.width;
      final yPos = (doorDetection.position.centerY / _latestDetection!.frameSize.height) * 
                   MediaQuery.of(context).size.height;
      
      // Verify coordinates are valid (not NaN or Infinity)
      if (!xPos.isFinite || !yPos.isFinite) {
        return const SizedBox.shrink();
      }

      IconData iconData;
      Color color;

      switch (_latestDetection!.navigation.arrow!.toUpperCase()) {
        case 'LEFT':
          iconData = Icons.arrow_back;
          color = Colors.orangeAccent;
          break;
        case 'RIGHT':
          iconData = Icons.arrow_forward;
          color = Colors.orangeAccent;
          break;
        case 'FORWARD':
          iconData = Icons.arrow_upward;
          color = Colors.greenAccent;
          break;
        default:
          return const SizedBox.shrink();
      }

      return Positioned(
        left: xPos - 40,
        top: yPos - 80,
        child: Container(
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.8),
            shape: BoxShape.circle,
            border: Border.all(color: color, width: 3),
            boxShadow: [
              BoxShadow(
                color: color.withOpacity(0.7),
                blurRadius: 20,
                spreadRadius: 3,
              ),
            ],
          ),
          child: Icon(
            iconData,
            size: 50,
            color: color,
          ),
        ),
      );
    }

    // Fallback: show arrow at bottom center
    return Positioned(
      bottom: 100,
      left: 0,
      right: 0,
      child: Center(
        child: NavigationArrow(
          direction: _latestDetection!.navigation.arrow,
        ),
      ),
    );
  }

  Widget _buildCameraPreview() {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.white),
      );
    }

    return SizedBox.expand(
      child: CameraPreview(_cameraController!),
    );
  }

  Widget _buildStatusBar() {
    return Positioned(
      top: 10,
      left: 10,
      right: 10,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.75),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _isBackendHealthy ? Colors.green.withOpacity(0.5) : Colors.red.withOpacity(0.5),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: _isBackendHealthy ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
              blurRadius: 8,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // First row: Backend status and refresh
            Row(
              children: [
                // Backend status
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: _isBackendHealthy ? Colors.green : Colors.red,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: _isBackendHealthy ? Colors.green : Colors.red,
                        blurRadius: 5,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _isBackendHealthy ? 'Backend Connected' : 'Backend Offline',
                      style: TextStyle(
                        color: _isBackendHealthy ? Colors.greenAccent : Colors.redAccent,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Text(
                      'Unified',
                      style: TextStyle(
                        color: Colors.cyanAccent,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                
                // Processing indicator
                if (_isProcessing)
                  Row(
                    children: [
                      const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.cyan,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.cyan),
                        ),
                      ),
                      const SizedBox(width: 6),
                      const Text(
                        'Processing',
                        style: TextStyle(
                          color: Colors.cyan,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                
                const SizedBox(width: 12),
                
                // Refresh button
                GestureDetector(
                  onTap: _checkBackendHealth,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: Colors.indigo.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Icon(
                      Icons.refresh,
                      color: Colors.cyan,
                      size: 16,
                    ),
                  ),
                ),
              ],
            ),
            
            // Second row: Detection count
            if (_latestDetection != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Row(
                  children: [
                    const Icon(
                      Icons.visibility,
                      size: 12,
                      color: Colors.amber,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '${_latestDetection!.detections.length} object${_latestDetection!.detections.length != 1 ? 's' : ''} detected',
                      style: const TextStyle(
                        color: Colors.amber,
                        fontSize: 11,
                      ),
                    ),
                    const Spacer(),
                    // Voice indicator
                    if (_voiceService.isSpeaking)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.3),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.volume_up,
                              size: 11,
                              color: Colors.red,
                            ),
                            SizedBox(width: 4),
                            Text(
                              'Speaking...',
                              style: TextStyle(
                                color: Colors.red,
                                fontSize: 10,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// Build control panel at the bottom
  Widget _buildControlPanel() {
    return Positioned(
      bottom: 10,
      left: 10,
      right: 10,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.75),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.indigo.withOpacity(0.5),
            width: 1.5,
          ),
        ),
        child: Row(
          children: [
            // Info Icon
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.indigo.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.info_outline,
                size: 18,
                color: Colors.cyan,
              ),
            ),
            const SizedBox(width: 12),
            
            // Status text
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'AI Navigation Assistant',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _isBackendHealthy
                        ? 'Ready – ${_currentModel.toUpperCase()}'
                        : 'Offline – Check backend',
                    style: TextStyle(
                      color: _isBackendHealthy ? Colors.greenAccent : Colors.redAccent,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ),
            
            const Spacer(),
            
            // Model Switcher Dropdown
            if (_isBackendHealthy)
              PopupMenuButton<String>(
                onSelected: (model) {
                  if (model != _currentModel) {
                    _switchModel(model);
                  }
                },
                itemBuilder: (BuildContext context) => [
                  PopupMenuItem(
                    value: 'custom',
                    child: Row(
                      children: [
                        Icon(
                          Icons.check_circle,
                          color: _currentModel == 'custom' ? Colors.green : Colors.grey,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        const Text('Custom Model'),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'yolov8n',
                    child: Row(
                      children: [
                        Icon(
                          Icons.check_circle,
                          color: _currentModel == 'yolov8n' ? Colors.green : Colors.grey,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        const Text('YOLOv8n'),
                      ],
                    ),
                  ),
                ],
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    _isSwitchingModel ? Icons.auto_awesome : Icons.model_training,
                    size: 18,
                    color: _isSwitchingModel ? Colors.yellow : Colors.orangeAccent,
                  ),
                ),
              ),
            const SizedBox(width: 8),
            
            // Mute voice button
            GestureDetector(
              onTap: () {
                _voiceService.stop();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Voice muted'),
                    duration: Duration(milliseconds: 800),
                    backgroundColor: Colors.indigo,
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.volume_off,
                  size: 18,
                  color: Colors.redAccent,
                ),
              ),
            ),
            const SizedBox(width: 8),

            // Debug Visualization button
            GestureDetector(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => DebugVisualizationScreen(),
                  ),
                );
              },
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.purple.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.videocam,
                  size: 18,
                  color: Colors.purpleAccent,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  double _sensorPanelBottomOffset(BuildContext context) {
    final h = MediaQuery.of(context).size.height;

    // Control panel is bottom:10 with ~70px height. Keep this panel
    // directly above it with a clean gap and no overlap.
    if (h < 700) return 92;
    if (h < 800) return 98;
    return 104;
  }

  /// Sensor TTS when heading/tilt changed meaningfully and cooldown elapsed.
  void _onSensorNavigationStateChanged(NavigationState s) {
    if (s.direction == NavDirection.none) return;

    final now = DateTime.now();
    const cooldown = Duration(seconds: 12);
    final since = _lastSensorGuidanceVoiceAt == null
        ? cooldown
        : now.difference(_lastSensorGuidanceVoiceAt!);

    final hDelta = _lastSensorVoiceHeading == null
        ? 999.0
        : _circularDiffDegrees(s.heading, _lastSensorVoiceHeading!);
    final tDelta = _lastSensorVoiceTilt == null
        ? 999.0
        : (s.tiltAngle - _lastSensorVoiceTilt!).abs();
    final significantMotion = hDelta >= 22.0 || tDelta >= 12.0;
    final dirChanged = _lastSensorVoiceDir != s.direction;

    if (dirChanged) {
      if (since < cooldown && !significantMotion) return;
    } else {
      if (!significantMotion || since < cooldown) return;
    }

    final msg = switch (s.direction) {
      NavDirection.left => 'Turn left',
      NavDirection.right => 'Turn right',
      NavDirection.forward => 'Go straight',
      NavDirection.none => '',
    };
    if (msg.isEmpty) return;

    _voiceService.speak(msg, 'sensor_nav', cooldownSeconds: 0);
    print('🧭 Sensor voice: $msg (${s.direction.name})');

    _lastSensorVoiceHeading = s.heading;
    _lastSensorVoiceTilt = s.tiltAngle;
    _lastSensorVoiceDir = s.direction;
    _lastSensorGuidanceVoiceAt = now;
  }
}
