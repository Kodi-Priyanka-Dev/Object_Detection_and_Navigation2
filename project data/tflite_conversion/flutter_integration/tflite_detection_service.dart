
import 'dart:typed_data';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;
import 'package:flutter/services.dart';

class TFLiteDetectionService {
  late Interpreter _customInterpreter;
  late Interpreter _yolov8nInterpreter;
  
  late Interpreter _currentInterpreter;
  String _currentModel = 'custom';
  
  // Model paths
  final String customModelPath = 'assets/models/custom_best.tflite';
  final String yolov8nModelPath = 'assets/models/yolov8n.tflite';
  
  // Input sizes (may differ between models)
  final Map<String, int> inputSizes = {
    'custom': 416,
    'yolov8n': 640,
  };
  
  // Class labels for each model
  final Map<String, List<String>> classLabels = {
    'custom': [
      'Digital Board', 'Door', 'Glass Door', 'Machine', 'Table',
      'chair', 'chairs', 'flowervase', 'human', 'humans',
      'round chair', 'sofa', 'stand', 'wall', 'wall corner',
      'wall edge', 'water filter', 'window', 'wooden entrance', 'wooden stand'
    ],
    'yolov8n': [
      'person', 'bicycle', 'car', 'motorcycle', 'airplane',
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
      'toilet', 'tv', 'laptop', 'mouse', 'remote',
      'keyboard', 'microwave', 'oven', 'toaster', 'sink',
      'refrigerator', 'book', 'clock', 'vase', 'scissors',
      'teddy bear', 'hair drier', 'toothbrush'
    ]
  };
  
  Future<void> loadModel(String modelName) async {
    try {
      print('🔄 Loading $modelName model...');
      
      if (modelName == 'custom') {
        try {
          _customInterpreter = await Interpreter.fromAsset(customModelPath);
          _currentInterpreter = _customInterpreter;
          print('✅ Custom model loaded successfully');
        } catch (e) {
          print('❌ Failed to load custom model: $e');
          print('   Ensure $customModelPath exists in assets/models/');
          rethrow;
        }
      } else if (modelName == 'yolov8n') {
        try {
          _yolov8nInterpreter = await Interpreter.fromAsset(yolov8nModelPath);
          _currentInterpreter = _yolov8nInterpreter;
          print('✅ YOLOv8n model loaded successfully');
        } catch (e) {
          print('❌ Failed to load YOLOv8n model: $e');
          print('   Ensure $yolov8nModelPath exists in assets/models/');
          rethrow;
        }
      } else {
        throw Exception('Unknown model: $modelName');
      }
      
      _currentModel = modelName;
    } catch (e) {
      print('❌ Model loading failed: $e');
      rethrow;
    }
  }
  
  Future<bool> switchModel(String modelName) async {
    try {
      if (modelName == _currentModel) {
        print('⚠️  Already using $modelName model');
        return true;
      }
      
      // Try to load if not already loaded
      if (modelName == 'custom') {
        if (_customInterpreter == null) {
          print('ℹ️  Custom model not pre-loaded, loading now...');
          try {
            await loadModel('custom');
          } catch (e) {
            print('❌ Failed to load custom model: $e');
            return false;
          }
        }
        _currentInterpreter = _customInterpreter;
      } else if (modelName == 'yolov8n') {
        if (_yolov8nInterpreter == null) {
          print('ℹ️  YOLOv8n model not pre-loaded, loading now...');
          try {
            await loadModel('yolov8n');
          } catch (e) {
            print('❌ Failed to load YOLOv8n model: $e');
            return false;
          }
        }
        _currentInterpreter = _yolov8nInterpreter;
      } else {
        print('❌ Unknown model: $modelName');
        return false;
      }
      
      _currentModel = modelName;
      print('✅ Switched to $modelName model');
      return true;
    } catch (e) {
      print('❌ Failed to switch model: $e');
      return false;
    }
  }
  
  String getCurrentModel() => _currentModel;
  
  Future<DetectionResult> detectObjects(Uint8List imageData) async {
    try {
      // Prepare input tensor
      var inputImage = img.decodeImage(imageData);
      if (inputImage == null) throw Exception('Failed to decode image');
      
      int inputSize = inputSizes[_currentModel] ?? 416;
      
      // Resize to model input size
      var resized = img.copyResize(inputImage,
          width: inputSize, height: inputSize);
      
      // Normalize pixel values
      var bytes = Float32List(1 * inputSize * inputSize * 3);
      var pixelIndex = 0;
      for (int i = 0; i < resized.height; i++) {
        for (int j = 0; j < resized.width; j++) {
          var pixel = resized.getPixelSafe(j, i);
          bytes[pixelIndex++] = img.getRed(pixel).toDouble() / 255.0;
          bytes[pixelIndex++] = img.getGreen(pixel).toDouble() / 255.0;
          bytes[pixelIndex++] = img.getBlue(pixel).toDouble() / 255.0;
        }
      }
      
      // Prepare output based on model
      List? output;
      if (_currentModel == 'custom') {
        output = List.filled(25200 * 25, 0.0).reshape([1, 25200, 25]);
      } else {
        output = List.filled(25200 * 85, 0.0).reshape([1, 25200, 85]); // YOLOv8n has more classes
      }
      
      final startTime = DateTime.now();
      _currentInterpreter.run(bytes, output);
      final inferenceTime = DateTime.now().difference(startTime).inMilliseconds;
      
      // Parse detections
      List<Detection> detections = _parseDetections(output[0] as List);
      
      return DetectionResult(
        detections: detections,
        inferenceTime: inferenceTime,
        model: _currentModel,
      );
    } catch (e) {
      print('❌ Inference error: $e');
      rethrow;
    }
  }
  
  List<Detection> _parseDetections(List rawOutput) {
    List<Detection> detections = [];
    List<String> labels = classLabels[_currentModel] ?? [];
    
    for (var prediction in rawOutput) {
      double confidence = prediction[4] as double;
      
      if (confidence > 0.35) {  // Dynamic confidence threshold
        detections.add(Detection(
          x: prediction[0] as double,
          y: prediction[1] as double,
          width: prediction[2] as double,
          height: prediction[3] as double,
          confidence: confidence,
          classLabel: _getClassLabel(prediction, labels),
        ));
      }
    }
    
    return detections;
  }
  
  String _getClassLabel(List prediction, List<String> labels) {
    double maxConf = 0;
    int maxIdx = 0;
    
    for (int i = 5; i < prediction.length; i++) {
      if (prediction[i] > maxConf) {
        maxConf = prediction[i];
        maxIdx = i - 5;
      }
    }
    
    return maxIdx < labels.length ? labels[maxIdx] : 'unknown';
  }
  
  void dispose() {
    try {
      _customInterpreter.close();
    } catch (e) {
      print('Error closing custom interpreter: $e');
    }
    try {
      _yolov8nInterpreter.close();
    } catch (e) {
      print('Error closing yolov8n interpreter: $e');
    }
  }
}

class Detection {
  final double x, y, width, height, confidence;
  final String classLabel;
  
  Detection({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.confidence,
    required this.classLabel,
  });
}

class DetectionResult {
  final List<Detection> detections;
  final int inferenceTime;
  final String model;
  
  DetectionResult({
    required this.detections,
    required this.inferenceTime,
    required this.model,
  });
}
