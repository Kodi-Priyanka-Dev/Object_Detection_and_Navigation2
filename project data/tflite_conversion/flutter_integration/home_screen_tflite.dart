import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'dart:async';
import 'dart:typed_data';
import 'tflite_detection_service.dart';

class TFLiteHomeScreen extends StatefulWidget {
  final List<CameraDescription> cameras;
  final TFLiteDetectionService detectionService;

  const TFLiteHomeScreen({
    Key? key,
    required this.cameras,
    required this.detectionService,
  }) : super(key: key);

  @override
  State<TFLiteHomeScreen> createState() => _TFLiteHomeScreenState();
}

class _TFLiteHomeScreenState extends State<TFLiteHomeScreen> with WidgetsBindingObserver {
  CameraController? _cameraController;
  bool _isProcessing = false;
  DetectionResult? _latestDetection;
  Timer? _detectionTimer;
  int _frameSkipCounter = 0;
  static const int FRAME_SKIP = 3; // Process every 3rd frame for TFLite
  
  String _currentModel = 'custom';
  bool _isSwitchingModel = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _detectionTimer?.cancel();
    _stopCameraStream();
    try {
      _cameraController?.dispose();
    } catch (e) {
      print('Error disposing camera: $e');
    }
    super.dispose();
  }

  void _stopCameraStream() {
    if (!mounted) return;
    try {
      _cameraController?.stopImageStream();
      _isProcessing = false;
    } catch (e) {
      if (!e.toString().contains('already stopped')) {
        print('Error stopping camera stream: $e');
      }
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!mounted) return;

    switch (state) {
      case AppLifecycleState.paused:
        print('🛑 App paused - stopping camera stream');
        _detectionTimer?.cancel();
        _stopCameraStream();
        break;

      case AppLifecycleState.resumed:
        print('▶️  App resumed - restarting camera stream');
        if (_cameraController != null && _cameraController!.value.isInitialized && mounted) {
          try {
            _startDetectionStream();
          } catch (e) {
            print('Error resuming camera stream: $e');
          }
        }
        break;

      case AppLifecycleState.detached:
        print('⏹️  App detached - emergency shutdown');
        _detectionTimer?.cancel();
        _stopCameraStream();
        break;

      case AppLifecycleState.hidden:
      case AppLifecycleState.inactive:
        break;
    }
  }

  Future<void> _initializeCamera() async {
    if (widget.cameras.isEmpty) {
      print('No cameras available');
      return;
    }

    _cameraController = CameraController(
      widget.cameras[0],
      ResolutionPreset.high,
      enableAudio: false,
    );

    try {
      await _cameraController!.initialize();
      
      if (mounted) {
        setState(() {});
        _startDetectionStream();
      }
    } catch (e) {
      print('Camera initialization error: $e');
    }
  }

  void _startDetectionStream() {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    try {
      _cameraController!.startImageStream((CameraImage image) {
        _frameSkipCounter++;
        if (_frameSkipCounter < FRAME_SKIP) {
          return;
        }
        _frameSkipCounter = 0;
        _onImageAvailable(image);
      });
    } catch (e) {
      print('Error starting image stream: $e');
    }
  }

  void _onImageAvailable(CameraImage cameraImage) async {
    if (!mounted || _isProcessing) return;

    if (mounted) {
      setState(() {
        _isProcessing = true;
      });
    }

    try {
      // Convert CameraImage to JPEG bytes (simplified)
      Uint8List imageBytes = _convertCameraImageToBytes(cameraImage);
      
      final response = await widget.detectionService.detectObjects(imageBytes);

      if (response != null && mounted) {
        print('📊 Detection | Model: ${response.model} | Objects: ${response.detections.length} | Time: ${response.inferenceTime}ms');

        setState(() {
          _latestDetection = response;
          _currentModel = response.model;
        });
      }
    } catch (e) {
      print('Detection error: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });
      }
    }
  }

  Uint8List _convertCameraImageToBytes(CameraImage image) {
    // Simplified conversion - for production use proper image conversion
    return image.planes[0].bytes;
  }

  Future<void> _switchModel(String modelName) async {
    if (_isSwitchingModel) return;

    setState(() {
      _isSwitchingModel = true;
    });

    try {
      final success = await widget.detectionService.switchModel(modelName);

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
              success ? '✅ Switched to $modelName' : '❌ Failed to switch model',
            ),
            duration: const Duration(seconds: 2),
            backgroundColor: success ? Colors.green : Colors.red,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSwitchingModel = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
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
            if (_cameraController != null && _cameraController!.value.isInitialized)
              CameraPreview(_cameraController!)
            else
              const Center(
                child: CircularProgressIndicator(),
              ),

            // Detection Results Overlay
            if (_latestDetection != null && _latestDetection!.detections.isNotEmpty)
              Positioned(
                top: 100,
                left: 10,
                right: 10,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.cyan, width: 1),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Model: ${_latestDetection!.model.toUpperCase()}',
                        style: const TextStyle(
                          color: Colors.cyanAccent,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      for (var det in _latestDetection!.detections.take(5))
                        Text(
                          '${det.classLabel}: ${(det.confidence * 100).toStringAsFixed(0)}%',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                          ),
                        ),
                      const SizedBox(height: 8),
                      Text(
                        'Inference: ${_latestDetection!.inferenceTime}ms',
                        style: const TextStyle(
                          color: Colors.yellowAccent,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            // Status Bar (Top)
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.6),
                  border: Border(
                    bottom: BorderSide(
                      color: Colors.indigo.withOpacity(0.3),
                      width: 1,
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: Colors.cyan,
                      size: 18,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'TFLite Navigation',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Model: ${_currentModel.toUpperCase()} | Processing: ${_isProcessing ? "ON" : "OFF"}',
                            style: const TextStyle(
                              color: Colors.greenAccent,
                              fontSize: 9,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Control Panel (Bottom)
            Positioned(
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
                    const Icon(
                      Icons.model_training,
                      color: Colors.orangeAccent,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Model: ${_currentModel.toUpperCase()}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const Spacer(),
                    // Model Switcher Dropdown
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
                                color: _currentModel == 'custom'
                                    ? Colors.green
                                    : Colors.grey,
                                size: 16,
                              ),
                              const SizedBox(width: 8),
                              const Text('Custom Model (20 classes)'),
                            ],
                          ),
                        ),
                        PopupMenuItem(
                          value: 'yolov8n',
                          child: Row(
                            children: [
                              Icon(
                                Icons.check_circle,
                                color: _currentModel == 'yolov8n'
                                    ? Colors.green
                                    : Colors.grey,
                                size: 16,
                              ),
                              const SizedBox(width: 8),
                              const Text('YOLOv8n (80 classes)'),
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
                          _isSwitchingModel
                              ? Icons.hourglass_empty
                              : Icons.swap_horiz,
                          size: 18,
                          color: _isSwitchingModel
                              ? Colors.yellow
                              : Colors.orangeAccent,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
