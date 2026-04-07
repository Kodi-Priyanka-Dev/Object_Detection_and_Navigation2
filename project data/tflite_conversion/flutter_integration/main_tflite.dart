import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'tflite_detection_service.dart';
import 'home_screen_tflite.dart';

late List<CameraDescription> cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Get available cameras
  cameras = await availableCameras();
  
  // Initialize TFLite service with model switching support
  final detectionService = TFLiteDetectionService();
  
  print('=" * 60);
  print('TFLITE MOBILE APP STARTUP');
  print('=" * 60);
  
  try {
    // Load custom model first (default)
    print('[1/2] Loading Custom model...');
    await detectionService.loadModel('custom');
    
    // Pre-load YOLOv8n for faster switching
    print('[2/2] Pre-loading YOLOv8n model...');
    await detectionService.loadModel('yolov8n');
    
    print('✅ All models loaded successfully!');
    print('Current model: ${detectionService.getCurrentModel()}');
    print('=" * 60);
  } catch (e) {
    print('❌ Error loading models: $e');
    print('The app may not function properly.');
  }
  
  runApp(MyApp(
    cameras: cameras,
    detectionService: detectionService,
  ));
}

class MyApp extends StatelessWidget {
  final List<CameraDescription> cameras;
  final TFLiteDetectionService detectionService;
  
  const MyApp({
    Key? key,
    required this.cameras,
    required this.detectionService,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TFLite Navigation Assistant',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      themeMode: ThemeMode.dark,
      home: TFLiteHomeScreen(
        cameras: cameras,
        detectionService: detectionService,
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}
