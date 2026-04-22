import 'package:tflite_flutter/tflite_flutter.dart';
import 'dart:math';
import 'dart:typed_data';

/// TFLite Detection Result
class DetectionResult {
  final double x;
  final double y;
  final double width;
  final double height;
  final double confidence;
  final String label;
  final int classId;

  DetectionResult({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.confidence,
    required this.label,
    required this.classId,
  });
}

/// TFLite Service for YOLOv8 Object Detection
class TFLiteService {
  late Interpreter _interpreter;
  bool _isInitialized = false;
  String _currentModel = 'yolov8n'; // 'yolov8n' or 'best'
  
  // Model input/output specs
  final int inputSize = 416;
  final double confidenceThreshold = 0.5;
  final double nmsThreshold = 0.6;

  // COCO class names (80 classes)
  static const List<String> cocoClasses = [
    'person', 'bicycle', 'car', 'motorbike', 'aeroplane',
    'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant',
    'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis',
    'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass',
    'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli',
    'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'couch', 'potted plant', 'bed', 'dining table',
    'toilet', 'tvmonitor', 'laptop', 'mouse', 'remote',
    'keyboard', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors',
    'teddy bear', 'hair drier', 'toothbrush'
  ];

  /// Initialize TFLite interpreter with specified model
  Future<bool> initializeModel(String modelType) async {
    try {
      if (_isInitialized && _currentModel == modelType) {
        return true; // Already initialized with same model
      }

      // Try to load the selected model
      String modelPath = modelType == 'yolov8n'
          ? 'assets/models/yolov8n.tflite'
          : 'assets/models/best.tflite';

      _interpreter = await Interpreter.fromAsset(modelPath);
      _currentModel = modelType;
      _isInitialized = true;

      print('✅ TFLite Model Loaded: $modelType');
      return true;
    } catch (e) {
      print('❌ Error initializing TFLite: $e');
      return false;
    }
  }

  /// Switch to a different model
  Future<bool> switchModel(String modelType) async {
    try {
      if (_isInitialized) {
        _interpreter.close();
      }
      return await initializeModel(modelType);
    } catch (e) {
      print('❌ Error switching model: $e');
      return false;
    }
  }

  /// Get current model name
  String getCurrentModel() => _currentModel;

  /// Get model initialization status
  bool isInitialized() => _isInitialized;

  /// Run inference on image data
  Future<List<DetectionResult>> runInference(Uint8List imageBytes, int imageWidth, int imageHeight) async {
    try {
      if (!_isInitialized) {
        throw Exception('Model not initialized');
      }

      // Prepare input tensor (4D: [1, 416, 416, 3])
      var resizedImage = _resizeImage(imageBytes, imageWidth, imageHeight);
      var inputTensor = Float32List.fromList(resizedImage);
      inputTensor = _normalizeImage(inputTensor);

      // Prepare output buffers
      var outputLocations = List<double>.filled(1 * 84 * 3549, 0).reshape([1, 84, 3549]);

      // Run inference
      _interpreter.run([inputTensor.reshape([1, 416, 416, 3])], [outputLocations]);

      // Post-process results
      List<DetectionResult> detections = _postProcess(outputLocations, imageWidth, imageHeight);
      
      return detections;
    } catch (e) {
      print('❌ Error running inference: $e');
      return [];
    }
  }

  /// Resize image to model input size
  List<double> _resizeImage(Uint8List imageBytes, int originalWidth, int originalHeight) {
    List<double> resized = List<double>.filled(inputSize * inputSize * 3, 0);
    
    // Calculate resize ratio
    double scaleX = inputSize / originalWidth;
    double scaleY = inputSize / originalHeight;
    double scale = min(scaleX, scaleY);

    int newWidth = (originalWidth * scale).toInt();
    int newHeight = (originalHeight * scale).toInt();

    // Simple nearest neighbor resizing
    int idx = 0;
    for (int c = 0; c < 3; c++) {
      for (int y = 0; y < inputSize; y++) {
        for (int x = 0; x < inputSize; x++) {
          int originalX = min((x / scale).toInt(), originalWidth - 1);
          int originalY = min((y / scale).toInt(), originalHeight - 1);
          int pixelIdx = (originalY * originalWidth + originalX) * 3 + c;
          
          if (pixelIdx < imageBytes.length) {
            resized[idx++] = imageBytes[pixelIdx].toDouble();
          } else {
            resized[idx++] = 0;
          }
        }
      }
    }
    return resized;
  }

  /// Normalize image (convert 0-255 to 0-1)
  Float32List _normalizeImage(Float32List data) {
    for (int i = 0; i < data.length; i++) {
      data[i] = data[i] / 255.0;
    }
    return data;
  }

  /// Post-process YOLOv8 output
  List<DetectionResult> _postProcess(List<List<List<double>>> output, int imageWidth, int imageHeight) {
    List<DetectionResult> detections = [];

    // YOLOv8 output format: [batch, 84, 3549]
    // 84 = 4 bbox coords + 80 class confidences
    var predictions = output[0];

    for (int i = 0; i < predictions[0].length; i++) {
      var pred = predictions.map((row) => row[i]).toList();

      // Extract coordinates and confidence
      double centerX = pred[0];
      double centerY = pred[1];
      double width = pred[2];
      double height = pred[3];

      // Get maximum class confidence
      double maxConfidence = 0;
      int classId = 0;

      for (int c = 4; c < pred.length; c++) {
        if (pred[c] > maxConfidence) {
          maxConfidence = pred[c];
          classId = c - 4;
        }
      }

      if (maxConfidence >= confidenceThreshold) {
        // Scale back to original image size
        double scaleX = imageWidth / inputSize;
        double scaleY = imageHeight / inputSize;

        detections.add(DetectionResult(
          x: centerX * scaleX - (width * scaleX / 2),
          y: centerY * scaleY - (height * scaleY / 2),
          width: width * scaleX,
          height: height * scaleY,
          confidence: maxConfidence,
          label: cocoClasses[min(classId, cocoClasses.length - 1)],
          classId: classId,
        ));
      }
    }

    // Apply NMS (Non-Maximum Suppression)
    return _nms(detections);
  }

  /// Non-Maximum Suppression to remove duplicate detections
  List<DetectionResult> _nms(List<DetectionResult> detections) {
    if (detections.isEmpty) return [];

    // Sort by confidence
    detections.sort((a, b) => b.confidence.compareTo(a.confidence));

    List<DetectionResult> kept = [];
    List<bool> suppressed = List<bool>.filled(detections.length, false);

    for (int i = 0; i < detections.length; i++) {
      if (suppressed[i]) continue;

      kept.add(detections[i]);

      for (int j = i + 1; j < detections.length; j++) {
        if (suppressed[j]) continue;

        double iou = _calculateIoU(detections[i], detections[j]);
        if (iou > nmsThreshold) {
          suppressed[j] = true;
        }
      }
    }

    return kept;
  }

  /// Calculate IoU (Intersection over Union) between two detections
  double _calculateIoU(DetectionResult box1, DetectionResult box2) {
    // Convert center coordinates to corner coordinates
    double x1_min = box1.x;
    double y1_min = box1.y;
    double x1_max = box1.x + box1.width;
    double y1_max = box1.y + box1.height;

    double x2_min = box2.x;
    double y2_min = box2.y;
    double x2_max = box2.x + box2.width;
    double y2_max = box2.y + box2.height;

    // Calculate intersection
    double intersect_x_min = max(x1_min, x2_min);
    double intersect_y_min = max(y1_min, y2_min);
    double intersect_x_max = min(x1_max, x2_max);
    double intersect_y_max = min(y1_max, y2_max);

    if (intersect_x_max < intersect_x_min || intersect_y_max < intersect_y_min) {
      return 0.0;
    }

    double intersection = (intersect_x_max - intersect_x_min) * (intersect_y_max - intersect_y_min);
    double area1 = box1.width * box1.height;
    double area2 = box2.width * box2.height;
    double union = area1 + area2 - intersection;

    return intersection / union;
  }

  /// Cleanup resources
  Future<void> close() async {
    if (_isInitialized) {
      _interpreter.close();
      _isInitialized = false;
    }
  }

  /// Get model information
  String getModelInfo() {
    if (!_isInitialized) return 'Model not loaded';
    
    var inputShape = _interpreter.getInputTensor(0).shape;
    var outputShape = _interpreter.getOutputTensor(0).shape;

    return '''
Model: $_currentModel
Input Shape: $inputShape
Output Shape: $outputShape
Confidence Threshold: $confidenceThreshold
NMS Threshold: $nmsThreshold
    ''';
  }
}
