import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';
import '../services/tflite_service.dart';
import '../widgets/detection_box.dart';
import 'dart:typed_data';
import 'dart:async';

class DetectionScreen extends StatefulWidget {
  final List<CameraDescription> cameras;

  const DetectionScreen({
    super.key,
    required this.cameras,
  });

  @override
  State<DetectionScreen> createState() => _DetectionScreenState();
}

class _DetectionScreenState extends State<DetectionScreen> {
  late CameraController _cameraController;
  late TFLiteService _tfliteService;
  
  bool _isInitialized = false;
  bool _isDetecting = false;
  bool _isModelLoading = false;
  String _selectedModel = 'yolov8n';
  List<DetectionResult> _detections = [];
  
  int _frameCount = 0;
  late Stopwatch _stopwatch;
  double _fps = 0;

  @override
  void initState() {
    super.initState();
    _tfliteService = TFLiteService();
    _stopwatch = Stopwatch()..start();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      if (widget.cameras.isEmpty) {
        throw Exception('No cameras available');
      }

      _cameraController = CameraController(
        widget.cameras[0],
        ResolutionPreset.high,
        enableAudio: false,
      );

      await _cameraController.initialize();
      
      // Initialize TFLite with default model
      await _switchModel('yolov8n');

      if (!mounted) return;
      setState(() => _isInitialized = true);

      // Start frame processing
      _startFrameProcessing();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Camera initialization error: $e')),
        );
      }
    }
  }

  void _startFrameProcessing() async {
    _cameraController.startImageStream((CameraImage image) async {
      if (_isDetecting) return;

      _isDetecting = true;

      try {
        // Convert camera image to bytes
        final Uint8List imageBytes = _convertImageToBytes(image);

        // Run inference
        final detections = await _tfliteService.runInference(
          imageBytes,
          image.width,
          image.height,
        );

        if (mounted) {
          setState(() {
            _detections = detections;
            _frameCount++;
            if (_stopwatch.elapsedMilliseconds >= 1000) {
              _fps = _frameCount / (_stopwatch.elapsedMilliseconds / 1000);
              _frameCount = 0;
              _stopwatch.reset();
            }
          });
        }
      } catch (e) {
        debugPrint('Error processing frame: $e');
      } finally {
        _isDetecting = false;
      }
    });
  }

  Uint8List _convertImageToBytes(CameraImage image) {
    // Convert NV21 format camera image to RGB
    final int width = image.width;
    final int height = image.height;
    final Uint8List data = image.planes[0].bytes;

    final img.Image imgLib = img.Image.fromBytes(
      width: width,
      height: height,
      bytes: data.buffer,
      format: img.Format.uint8,
      rowStride: image.planes[0].bytesPerRow,
    );

    return Uint8List.fromList(img.encodeJpg(imgLib));
  }

  Future<void> _switchModel(String model) async {
    setState(() => _isModelLoading = true);

    try {
      final success = await _tfliteService.switchModel(model);
      
      if (success) {
        setState(() {
          _selectedModel = model;
          _detections = [];
        });
        
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Model switched to: ${model == 'yolov8n' ? 'YOLOv8n (Official)' : 'Custom Best'}'),
            duration: const Duration(seconds: 2),
          ),
        );
      } else {
        throw Exception('Model switch failed');
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error switching model: $e')),
      );
    } finally {
      setState(() => _isModelLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return Scaffold(
        appBar: AppBar(title: const Text('YOLOv8 Detection')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('🎯 YOLOv8 Object Detection'),
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Camera preview with detection overlays
          _buildCameraPreview(),
          
          // Top controls
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: _buildModelSwitcher(),
          ),

          // Bottom stats
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: _buildStats(),
          ),

          // Detection list
          Positioned(
            right: 0,
            top: 80,
            bottom: 100,
            width: 200,
            child: _buildDetectionList(),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraPreview() {
    return Stack(
      children: [
        CameraPreview(_cameraController),
        // Draw detection boxes
        CustomPaint(
          painter: DetectionPainter(
            detections: _detections,
            imageWidth: _cameraController.value.previewSize!.width,
            imageHeight: _cameraController.value.previewSize!.height,
          ),
          size: Size.infinite,
        ),
      ],
    );
  }

  Widget _buildModelSwitcher() {
    return Container(
      color: Colors.black.withOpacity(0.7),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            '📦 Select Model',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isModelLoading
                      ? null
                      : () => _switchModel('yolov8n'),
                  icon: const Icon(Icons.robot),
                  label: const Text('YOLOv8n'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _selectedModel == 'yolov8n'
                        ? Colors.blue
                        : Colors.grey[700],
                    disabledBackgroundColor: Colors.grey[600],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isModelLoading
                      ? null
                      : () => _switchModel('best'),
                  icon: const Icon(Icons.star),
                  label: const Text('Custom Best'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _selectedModel == 'best'
                        ? Colors.purple
                        : Colors.grey[700],
                    disabledBackgroundColor: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStats() {
    return Container(
      color: Colors.black.withOpacity(0.8),
      padding: const EdgeInsets.all(12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'FPS: ${_fps.toStringAsFixed(1)}',
                style: const TextStyle(
                  color: Colors.green,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Model: $_selectedModel',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          Text(
            'Detections: ${_detections.length}',
            style: const TextStyle(
              color: Colors.yellow,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          ElevatedButton.icon(
            onPressed: () => _showModelInfo(),
            icon: const Icon(Icons.info),
            label: const Text('Info'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.indigo,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetectionList() {
    return Container(
      color: Colors.black.withOpacity(0.8),
      child: ListView.builder(
        itemCount: _detections.length,
        itemBuilder: (context, index) {
          final detection = _detections[index];
          return Container(
            padding: const EdgeInsets.all(6),
            margin: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: _getColorForClass(detection.classId),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  detection.label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  '${(detection.confidence * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 9,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Color _getColorForClass(int classId) {
    const colors = [
      Colors.red,
      Colors.blue,
      Colors.green,
      Colors.yellow,
      Colors.purple,
      Colors.orange,
      Colors.pink,
      Colors.cyan,
    ];
    return colors[classId % colors.length];
  }

  void _showModelInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('📋 Model Information'),
        content: Text(
          _tfliteService.getModelInfo(),
          style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _cameraController.dispose();
    _tfliteService.close();
    _stopwatch.stop();
    super.dispose();
  }
}

/// Custom painter for drawing detection boxes
class DetectionPainter extends CustomPainter {
  final List<DetectionResult> detections;
  final double imageWidth;
  final double imageHeight;

  DetectionPainter({
    required this.detections,
    required this.imageWidth,
    required this.imageHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    const colors = [
      Colors.red,
      Colors.blue,
      Colors.green,
      Colors.yellow,
      Colors.purple,
      Colors.orange,
      Colors.pink,
      Colors.cyan,
    ];

    for (var detection in detections) {
      final color = colors[detection.classId % colors.length];
      
      // Scale detection coordinates to screen size
      final scaleX = size.width / imageWidth;
      final scaleY = size.height / imageHeight;

      final rect = Rect.fromLTWH(
        detection.x * scaleX,
        detection.y * scaleY,
        detection.width * scaleX,
        detection.height * scaleY,
      );

      // Draw bounding box
      canvas.drawRect(
        rect,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2,
      );

      // Draw label background
      final textPainter = TextPainter(
        text: TextSpan(
          text: '${detection.label} ${(detection.confidence * 100).toStringAsFixed(1)}%',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();

      final labelRect = Rect.fromLTWH(
        rect.left,
        rect.top - textPainter.height - 6,
        textPainter.width + 6,
        textPainter.height + 4,
      );

      canvas.drawRect(
        labelRect,
        Paint()..color = color,
      );

      textPainter.paint(canvas, Offset(labelRect.left + 3, labelRect.top + 2));
    }
  }

  @override
  bool shouldRepaint(DetectionPainter oldDelegate) =>
      detections != oldDelegate.detections;
}
