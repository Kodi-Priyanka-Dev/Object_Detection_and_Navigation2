import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:camera/camera.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';
import '../models/detection_model.dart';

/// Service for on-device TFLite object detection using YOLOv8n
class TFLiteDetectionService {
  static Interpreter? _interpreter;
  static final TFLiteDetectionService _instance = TFLiteDetectionService._internal();

  // Model constants
  static const String modelAsset = 'assets/models/yolov8n.tflite';
  static const int inputWidth = 416;
  static const int inputHeight = 416;
  static const int numClasses = 80; // COCO dataset classes
  static const double confThreshold = 0.35;
  static const double nmsThreshold = 0.45;

  // COCO class names
  static const List<String> cocoNames = [
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
    'teddy bear', 'hair drier', 'toothbrush', 'door', 'wall',
  ];

  TFLiteDetectionService._internal();

  factory TFLiteDetectionService() {
    return _instance;
  }

  /// Initialize the TFLite interpreter
  Future<bool> initialize() async {
    try {
      if (_interpreter != null) {
        print('ℹ️  TFLite interpreter already initialized');
        return true;
      }

      print('📥 Loading TFLite model: $modelAsset');

      // Load model from assets
      final modelData = await rootBundle.load(modelAsset);
      _interpreter = await Interpreter.fromBuffer(modelData.buffer.asUint8List());

      print('✅ TFLite model loaded successfully');
      print('   Input shape: [1, $inputHeight, $inputWidth, 3]');
      print('   Output layers: ${_interpreter!.getOutputTensors.length}');

      return true;
    } catch (e) {
      print('❌ Failed to initialize TFLite model: $e');
      return false;
    }
  }

  /// Detect objects in camera frame
  Future<DetectionResponse?> detectObjects(
    CameraImage cameraImage, {
    int rotationDegrees = 0,
    double confThreshold = 0.35,
  }) async {
    try {
      if (_interpreter == null) {
        print('❌ TFLite interpreter not initialized. Call initialize() first.');
        return null;
      }

      final startTime = DateTime.now();

      // Convert camera image to tensor input
      final input = _prepareInput(cameraImage, rotationDegrees);
      
      // Run inference
      final inferenceStart = DateTime.now();
      final outputs = <String, dynamic>{};
      _interpreter!.runForMultipleInputs([input], outputs);
      final inferenceDuration = DateTime.now().difference(inferenceStart).inMilliseconds;

      // Post-process results
      final detections = _parseOutput(
        outputs,
        cameraImage.width.toDouble(),
        cameraImage.height.toDouble(),
        confThreshold,
      );

      final totalDuration = DateTime.now().difference(startTime).inMilliseconds;
      print('⏱️  TFLite inference: ${inferenceDuration}ms | Total: ${totalDuration}ms');

      return DetectionResponse(
        success: true,
        detections: detections,
        navigation: Navigation(direction: 'STRAIGHT'),
        frameSize: FrameSize(width: cameraImage.width, height: cameraImage.height),
      );
    } catch (e) {
      print('❌ TFLite detection error: $e');
      return null;
    }
  }

  /// Prepare input tensor from camera image
  List<List<List<List<double>>>> _prepareInput(CameraImage image, int rotation) {
    // Convert image to Image package format
    final img_package = _convertCameraImageToImage(image);
    if (img_package == null) {
      return List.filled(1, List.filled(inputHeight, List.filled(inputWidth, List.filled(3, 0.0))));
    }

    // Resize to input size
    final resized = img.copyResize(img_package, width: inputWidth, height: inputHeight);

    // Normalize and convert to tensor
    final input = List.generate(
      1,
      (_) => List.generate(
        inputHeight,
        (y) => List.generate(
          inputWidth,
          (x) {
            final pixel = resized.getPixelRgbaSafe(x, y);
            final r = pixel.r.toDouble() / 255.0;
            final g = pixel.g.toDouble() / 255.0;
            final b = pixel.b.toDouble() / 255.0;
            return [r, g, b];
          },
        ),
      ),
    );

    return input;
  }

  /// Convert CameraImage to Image package format
  img.Image? _convertCameraImageToImage(CameraImage cameraImage) {
    try {
      if (cameraImage.format.group == ImageFormatGroup.yuv420) {
        return _convertYUV420ToImage(cameraImage);
      } else if (cameraImage.format.group == ImageFormatGroup.bgra8888) {
        return _convertBGRA8888ToImage(cameraImage);
      } else if (cameraImage.format.group == ImageFormatGroup.nv21) {
        return _convertNV21ToImage(cameraImage);
      }
      return null;
    } catch (e) {
      print('Image conversion error: $e');
      return null;
    }
  }

  /// Convert YUV420 to RGB Image
  img.Image? _convertYUV420ToImage(CameraImage cameraImage) {
    try {
      final int width = cameraImage.width;
      final int height = cameraImage.height;
      
      final yPlane = cameraImage.planes[0];
      final uPlane = cameraImage.planes[1];
      final vPlane = cameraImage.planes[2];
      
      final int yRowStride = yPlane.bytesPerRow;
      final int uvRowStride = uPlane.bytesPerRow;
      final int uvPixelStride = uPlane.bytesPerPixel ?? 1;
      
      final yBytes = yPlane.bytes;
      final uBytes = uPlane.bytes;
      final vBytes = vPlane.bytes;
      
      final image = img.Image(width: width, height: height);
      
      for (int y = 0; y < height; y += 2) {
        for (int x = 0; x < width; x += 2) {
          final uvIndex = uvPixelStride * (x ~/ 2) + uvRowStride * (y ~/ 2);
          final u = uBytes[uvIndex];
          final v = vBytes[uvIndex];
          
          _setYUVPixel(image, x, y, yBytes, yRowStride, u, v, width, height);
          if (x + 1 < width) _setYUVPixel(image, x + 1, y, yBytes, yRowStride, u, v, width, height);
          if (y + 1 < height) _setYUVPixel(image, x, y + 1, yBytes, yRowStride, u, v, width, height);
          if (x + 1 < width && y + 1 < height) _setYUVPixel(image, x + 1, y + 1, yBytes, yRowStride, u, v, width, height);
        }
      }
      
      return image;
    } catch (e) {
      print('YUV420 conversion error: $e');
      return null;
    }
  }

  /// Convert BGRA8888 to RGB Image
  img.Image? _convertBGRA8888ToImage(CameraImage cameraImage) {
    try {
      final int width = cameraImage.width;
      final int height = cameraImage.height;
      final bytes = cameraImage.planes[0].bytes;
      
      final image = img.Image(width: width, height: height);
      
      for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
          final int index = (y * width + x) * 4;
          final b = bytes[index];
          final g = bytes[index + 1];
          final r = bytes[index + 2];
          
          image.setPixelRgb(x, y, r, g, b);
        }
      }
      
      return image;
    } catch (e) {
      print('BGRA8888 conversion error: $e');
      return null;
    }
  }

  /// Convert NV21 to RGB Image (Android)
  img.Image? _convertNV21ToImage(CameraImage cameraImage) {
    try {
      final bytes = cameraImage.planes[0].bytes;
      final width = cameraImage.width;
      final height = cameraImage.height;
      
      final image = img.Image(width: width, height: height);
      
      final frameSize = width * height;
      
      for (int i = 0; i < frameSize; i++) {
        final y = (bytes[i].toInt() - 16) << 8;
        int u = bytes[frameSize + 2 * (i ~/ 2)].toInt() - 128;
        int v = bytes[frameSize + 2 * (i ~/ 2) + 1].toInt() - 128;
        
        int r = ((y + 409 * v + 128) >> 8).clamp(0, 255);
        int g = ((y - 100 * u - 208 * v + 128) >> 8).clamp(0, 255);
        int b = ((y + 516 * u + 128) >> 8).clamp(0, 255);
        
        int pixelIndex = i;
        int x = pixelIndex % width;
        int y_coord = pixelIndex ~/ width;
        
        image.setPixelRgb(x, y_coord, r, g, b);
      }
      
      return image;
    } catch (e) {
      print('NV21 conversion error: $e');
      return null;
    }
  }

  /// Helper to set YUV pixel
  void _setYUVPixel(img.Image image, int x, int y, Uint8List yBytes, int yRowStride,
      int u, int v, int width, int height) {
    if (x < width && y < height) {
      final yIndex = y * yRowStride + x;
      final yp = yBytes[yIndex];
      
      final c = yp - 16;
      final d = u - 128;
      final e = v - 128;
      
      int r = ((298 * c + 409 * e + 128) >> 8).clamp(0, 255);
      int g = ((298 * c - 100 * d - 208 * e + 128) >> 8).clamp(0, 255);
      int b = ((298 * c + 516 * d + 128) >> 8).clamp(0, 255);
      
      image.setPixelRgb(x, y, r, g, b);
    }
  }

  /// Parse TFLite output - simplified for YOLOv8n
  List<Detection> _parseOutput(
    Map<String, dynamic> outputs,
    double frameWidth,
    double frameHeight,
    double confThreshold,
  ) {
    final List<Detection> detections = [];

    try {
      // Get output tensor - YOLOv8n outputs shape [1, 84, 3549]
      // where 84 = 4(bbox) + 1(objectness) + 80(classes)
      final output = outputs.values.first as List;
      
      if (output.isEmpty) return detections;

      // Parse predictions
      final predictions = output[0]; // Shape: [84, 3549]
      
      for (int i = 0; i < 3549; i++) {
        // Extract objectness score
        final objConf = (predictions[4]?[i] as num?)?.toDouble() ?? 0.0;
        
        if (objConf < confThreshold) continue;

        // Find class with max confidence
        int classId = 0;
        double maxConfidence = 0;

        for (int j = 5; j < 85; j++) {
          final conf = (predictions[j]?[i] as num?)?.toDouble() ?? 0.0;
          if (conf > maxConfidence) {
            maxConfidence = conf;
            classId = j - 5;
          }
        }

        final confidence = objConf * maxConfidence;
        if (confidence < confThreshold) continue;

        // Extract bounding box
        final x = (predictions[0]?[i] as num?)?.toDouble() ?? 0.0;
        final y = (predictions[1]?[i] as num?)?.toDouble() ?? 0.0;
        final w = (predictions[2]?[i] as num?)?.toDouble() ?? 0.0;
        final h = (predictions[3]?[i] as num?)?.toDouble() ?? 0.0;

        final x1 = ((x - w / 2) * frameWidth / inputWidth).clamp(0.0, frameWidth);
        final y1 = ((y - h / 2) * frameHeight / inputHeight).clamp(0.0, frameHeight);
        final x2 = ((x + w / 2) * frameWidth / inputWidth).clamp(0.0, frameWidth);
        final y2 = ((y + h / 2) * frameHeight / inputHeight).clamp(0.0, frameHeight);

        detections.add(Detection(
          className: classId < cocoNames.length ? cocoNames[classId] : 'unknown',
          confidence: confidence,
          position: Position(
            x: x,
            y: y,
            x1: x1,
            y1: y1,
            x2: x2,
            y2: y2,
            centerX: (x1 + x2) / 2,
            centerY: (y1 + y2) / 2,
          ),
          distance: 0.0,
          width: (x2 - x1).toInt(),
          height: (y2 - y1).toInt(),
        ));
      }
    } catch (e) {
      print('Output parsing error: $e');
    }

    return detections;
  }

  /// Dispose interpreter
  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    print('✓ TFLite interpreter disposed');
  }

  /// Get model info
  String getModelInfo() {
    return 'YOLOv8n (TFLite)\nInput: ${inputWidth}x${inputHeight}\nClasses: $numClasses';
  }
}
