import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'dart:async';
import '../services/detection_service.dart';
import '../services/voice_service.dart';
import '../models/detection_model.dart';
import '../widgets/object_labels.dart';
import '../widgets/navigation_arrow.dart';
import '../widgets/navigation_popup.dart';

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
  
  bool _isProcessing = false;
  bool _isBackendHealthy = false;
  DetectionResponse? _latestDetection;
  Timer? _detectionTimer;
  int _frameSkipCounter = 0;
  static const int FRAME_SKIP = 1; // Process every 2nd frame for faster detection

  /// Currently active YOLO model.
  ModelType _activeModel = DetectionService.activeModel;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
    _checkBackendHealth();
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

  /// Cycle between available model backends.
  Future<void> _switchModel() async {
    final previous = _activeModel;
    final next = _activeModel == ModelType.custom
        ? ModelType.yolo26n
        : ModelType.custom;

    // Probe target backend first; do not commit switch if it is offline.
    DetectionService.switchModel(next);
    final isNextHealthy = await _detectionService.healthCheck();
    if (!mounted) return;

    if (!isNextHealthy) {
      DetectionService.switchModel(previous);
      setState(() {
        _activeModel = previous;
        _isBackendHealthy = true;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${next.label} backend is offline. Staying on ${previous.label}.'),
          duration: const Duration(milliseconds: 1800),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    setState(() {
      _activeModel = next;
      _isBackendHealthy = true;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Switched to ${next.label}'),
        duration: const Duration(milliseconds: 1200),
        backgroundColor: Colors.indigo,
      ),
    );
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
    final isHealthy = await _detectionService.healthCheck();
    if (mounted) {
      setState(() {
        _isBackendHealthy = isHealthy;
      });
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
        });

        // Handle voice guidance - prioritize popups
        if (response.navigation.popup != null) {
          final popup = response.navigation.popup!;
          print('🔊 POPUP TRIGGERED: ${popup.type} at ${popup.distance}m');
          print('📢 Speaking: ${popup.message}');
          
          await _voiceService.speak(
            popup.message,
            '${popup.type}_${popup.distance.toInt()}',
            cooldownSeconds: 2, // Faster repetition for popups
          );
        } else if (response.navigation.message != null) {
          // Only speak navigation messages if no popup exists
          print('📣 Navigation guidance: ${response.navigation.message}');
          await _voiceService.speak(
            response.navigation.message!,
            'nav_${response.navigation.direction}',
            cooldownSeconds: 4,
          );
        } else if (response.detections.isNotEmpty) {
          // Log detected objects even without popup/message
          final objectNames = response.detections
              .map((d) => '${d.className} (${d.confidence})')
              .join(', ');
          print('🎯 Detected objects: $objectNames');
        }
      } else if (response == null) {
        print('❌ Detection service returned null');
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
            
            // Navigation Arrow (positioned near door if detected)
            if (_latestDetection?.navigation.arrow != null)
              _buildNavigationArrow(),
            
            // Navigation Popup
            if (_latestDetection?.navigation.popup != null)
              Positioned(
                top: 80,
                left: 0,
                right: 0,
                child: NavigationPopupWidget(
                  popup: _latestDetection!.navigation.popup,
                ),
              ),
            
            // Status indicators (top)
            _buildStatusBar(),
            
            // Control Panel (bottom)
            _buildControlPanel(),
          ],
        ),
      ),
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
                    Text(
                      _activeModel.label,
                      style: const TextStyle(
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
                        ? 'Ready – ${_activeModel.label}'
                        : 'Offline – Check ${_activeModel.label} backend',
                    style: TextStyle(
                      color: _isBackendHealthy ? Colors.greenAccent : Colors.redAccent,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ),
            
            const Spacer(),
            
            // Model toggle button
            GestureDetector(
              onTap: _switchModel,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.indigo.withOpacity(0.35),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.cyanAccent.withOpacity(0.4)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.swap_horiz, size: 16, color: Colors.cyanAccent),
                    const SizedBox(width: 4),
                    Text(
                      _activeModel == ModelType.custom ? 'YOLO26n' : 'Custom',
                      style: const TextStyle(color: Colors.cyanAccent, fontSize: 11),
                    ),
                  ],
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
          ],
        ),
      ),
    );
  }
}
