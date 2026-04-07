
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
