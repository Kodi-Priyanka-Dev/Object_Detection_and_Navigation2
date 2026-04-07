"""
Flutter Integration Helper
Generates code snippets and configuration for integrating TFLite model
"""

import os

FLUTTER_DETECTION_SERVICE = '''
import 'dart:typed_data';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;
import 'package:flutter/services.dart';

class TFLiteDetectionService {
  late Interpreter interpreter;
  final String modelPath = 'assets/models/best.tflite';
  final int inputSize = 416;
  
  Future<void> loadModel() async {
    try {
      interpreter = await Interpreter.fromAsset(modelPath);
      print('✓ TFLite model loaded successfully');
    } catch (e) {
      print('✗ Failed to load TFLite model: $e');
      rethrow;
    }
  }
  
  Future<DetectionResult> detectObjects(Uint8List imageData) async {
    try {
      // Prepare input tensor
      var inputImage = img.decodeImage(imageData);
      if (inputImage == null) throw Exception('Failed to decode image');
      
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
      
      // Run inference
      var output = List.filled(25200 * 25, 0.0).reshape([1, 25200, 25]);
      
      interpreter.run(bytes, output);
      
      // Parse detections
      List<Detection> detections = _parseDetections(output[0] as List);
      
      return DetectionResult(
        detections: detections,
        inferenceTime: DateTime.now().millisecondsSinceEpoch,
      );
    } catch (e) {
      print('✗ Inference error: $e');
      rethrow;
    }
  }
  
  List<Detection> _parseDetections(List rawOutput) {
    List<Detection> detections = [];
    
    for (var prediction in rawOutput) {
      double confidence = prediction[4] as double;
      
      if (confidence > 0.5) {  // Confidence threshold
        detections.add(Detection(
          x: prediction[0] as double,
          y: prediction[1] as double,
          width: prediction[2] as double,
          height: prediction[3] as double,
          confidence: confidence,
          classLabel: _getClassLabel(prediction),
        ));
      }
    }
    
    return detections;
  }
  
  String _getClassLabel(List prediction) {
    // Update with your class labels
    List<String> classes = [
      'door', 'room', 'corridor', 'obstacle'
    ];
    
    double maxConf = 0;
    int maxIdx = 0;
    
    for (int i = 5; i < prediction.length; i++) {
      if (prediction[i] > maxConf) {
        maxConf = prediction[i];
        maxIdx = i - 5;
      }
    }
    
    return maxIdx < classes.length ? classes[maxIdx] : 'unknown';
  }
  
  void dispose() {
    interpreter.close();
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
  
  DetectionResult({
    required this.detections,
    required this.inferenceTime,
  });
}
'''

PUBSPEC_UPDATE = '''
# Add these dependencies to your pubspec.yaml:

dependencies:
  flutter:
    sdk: flutter
  tflite_flutter: ^0.10.0
  camera: ^0.10.5
  image: ^4.0.0
  permission_handler: ^11.4.0
  
  # Audio for voice navigation
  audioplayers: ^4.1.0
  text_to_speech: ^0.2.3
'''

MAIN_DART_UPDATE = '''
import 'package:flutter/material.dart';
import 'services/tflite_detection_service.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize TFLite service
  final detectionService = TFLiteDetectionService();
  await detectionService.loadModel();
  
  runApp(MyApp(detectionService: detectionService));
}

class MyApp extends StatelessWidget {
  final TFLiteDetectionService detectionService;
  
  const MyApp({required this.detectionService});
  
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Navigation Assistant',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: HomeScreen(detectionService: detectionService),
    );
  }
}
'''

ASSETS_STRUCTURE = '''
Flutter Project Structure for TFLite Assets:

your_app/
├── assets/
│   ├── models/
│   │   └── best.tflite          ← Copy your converted model here
│   ├── images/
│   └── sounds/
├── lib/
│   ├── services/
│   │   └── tflite_detection_service.dart
│   ├── screens/
│   │   └── home_screen.dart
│   └── main.dart
└── pubspec.yaml
'''

def generate_flutter_setup():
    """Generate Flutter setup guides"""
    
    print("\n" + "="*60)
    print("Flutter Integration Setup")
    print("="*60)
    
    # Create output directory
    os.makedirs("flutter_integration", exist_ok=True)
    
    # Write detection service
    with open("flutter_integration/tflite_detection_service.dart", "w", encoding="utf-8") as f:
        f.write(FLUTTER_DETECTION_SERVICE)
    print("[OK] Created: flutter_integration/tflite_detection_service.dart")
    
    # Write pubspec template
    with open("flutter_integration/pubspec_updates.txt", "w", encoding="utf-8") as f:
        f.write(PUBSPEC_UPDATE)
    print("[OK] Created: flutter_integration/pubspec_updates.txt")
    
    # Write main.dart template
    with open("flutter_integration/main_dart_template.dart", "w", encoding="utf-8") as f:
        f.write(MAIN_DART_UPDATE)
    print("[OK] Created: flutter_integration/main_dart_template.dart")
    
    # Write assets structure guide
    with open("flutter_integration/assets_structure.txt", "w", encoding="utf-8") as f:
        f.write(ASSETS_STRUCTURE)
    print("[OK] Created: flutter_integration/assets_structure.txt")
    
    print("\n" + "="*60)
    print("Flutter Integration Files Generated")
    print("="*60)
    print("\nNext steps:")
    print("1. Update your Flutter pubspec.yaml with dependencies")
    print("2. Copy tflite_detection_service.dart to lib/services/")
    print("3. Place best.tflite in assets/models/")
    print("4. Update main.dart with the template provided")
    print("5. Run: flutter pub get")
    print("6. Build and deploy to your device")

if __name__ == "__main__":
    generate_flutter_setup()
