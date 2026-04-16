import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:camera/camera.dart';
import 'package:image/image.dart' as img;
import '../models/detection_model.dart';

/// Service for communicating with the Flask backend
class DetectionService {
  // Backend URL - Update this to your computer's IP address
  static const String baseIP =
      String.fromEnvironment('BACKEND_IP', defaultValue: '10.26.68.112');
  static const int port = int.fromEnvironment('BACKEND_PORT', defaultValue: 5000);
  
  static String get baseUrl => 'http://$baseIP:$port';
  
  /// Check if backend is healthy
  Future<Map<String, dynamic>?> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✓ Backend health: ${data['status']} | Model: ${data['current_model']} | Classes: ${data['classes']}');
        return data;
      }
      return null;
    } catch (e) {
      print('Health check failed: $e');
      return null;
    }
  }

  /// Switch between custom and yolov8n models
  Future<bool> switchModel(String modelName) async {
    try {
      print('🔄 Switching to model: $modelName');
      final response = await http.post(
        Uri.parse('$baseUrl/switch-model'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'model': modelName}),
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Model switched to: ${data['current_model']} (${data['classes']} classes)');
        return true;
      } else {
        print('❌ Model switch failed: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      print('Model switch error: $e');
      return false;
    }
  }
  
  /// Handle door popup response (Yes/No)
  Future<Map<String, dynamic>?> handleDoorResponse({
    required String userResponse,
    required String doorClass,
    required double doorDistance,
  }) async {
    try {
      print('🚪 Sending door response to backend: $userResponse');
      final response = await http.post(
        Uri.parse('$baseUrl/handle_door_response'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'user_response': userResponse.toLowerCase(),
          'door_class': doorClass,
          'door_distance': doorDistance,
        }),
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✓ Door response handled: ${data['action']}');
        return data;
      } else {
        print('❌ Door response failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Door response error: $e');
      return null;
    }
  }

  /// Send frame for detection
  Future<DetectionResponse?> detectObjects(
    CameraImage cameraImage, {
    int rotationDegrees = 0,
  }) async {
    try {
      final startTime = DateTime.now();
      
      // Convert CameraImage to JPEG
      final convertStart = DateTime.now();
      final jpegBytes = await _convertCameraImageToJpeg(
        cameraImage,
        rotationDegrees: rotationDegrees,
      );
      final convertTime = DateTime.now().difference(convertStart).inMilliseconds;
      
      if (jpegBytes == null) {
        print('Failed to convert camera image');
        return null;
      }
      
      // Encode to base64
      final base64Image = base64Encode(jpegBytes);
      
      // Send to backend
      final sendStart = DateTime.now();
      final response = await http.post(
        Uri.parse('$baseUrl/detect'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'image': base64Image}),
      ).timeout(const Duration(seconds: 15)); // Increased timeout for higher quality images
      final sendTime = DateTime.now().difference(sendStart).inMilliseconds;
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final result = DetectionResponse.fromJson(data);
        
        final totalTime = DateTime.now().difference(startTime).inMilliseconds;
        print('⏱️  TIMING | Convert: ${convertTime}ms | Backend: ${sendTime}ms | Total: ${totalTime}ms');
        
        return result;
      } else {
        print('Detection failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Detection error: $e');
      return null;
    }
  }

  /// Convert CameraImage to JPEG bytes
  Future<Uint8List?> _convertCameraImageToJpeg(
    CameraImage cameraImage, {
    int rotationDegrees = 0,
  }) async {
    try {
      // Create image from camera data
      img.Image? image;
      
      if (cameraImage.format.group == ImageFormatGroup.yuv420) {
        image = _convertYUV420ToImage(cameraImage);
      } else if (cameraImage.format.group == ImageFormatGroup.bgra8888) {
        image = _convertBGRA8888ToImage(cameraImage);
      } else {
        print('Unsupported image format: ${cameraImage.format.group}');
        return null;
      }
      
      if (image == null) {
        return null;
      }

      // Rotate to correct sensor orientation (common: 90° on Android streams)
      final normalizedRotation = ((rotationDegrees % 360) + 360) % 360;
      if (normalizedRotation != 0) {
        image = img.copyRotate(image, angle: normalizedRotation);
      }
      
      // Resize for optimal speed and accuracy balance
      // 640x480 is ideal: fast processing + good detection accuracy
      final resized = img.copyResize(image, width: 640, height: 480);
      
      // Encode to JPEG with balanced quality (80) for faster transmission
      // Quality 80 is imperceptible to detection but ~30% smaller than 95
      return Uint8List.fromList(img.encodeJpg(resized, quality: 80));
    } catch (e) {
      print('Image conversion error: $e');
      return null;
    }
  }

  /// Convert YUV420 to RGB Image (optimized)
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
      
      // Process 2x2 blocks to be more efficient
      for (int y = 0; y < height; y += 2) {
        for (int x = 0; x < width; x += 2) {
          final uvIndex = uvPixelStride * (x ~/ 2) + uvRowStride * (y ~/ 2);
          
          final u = uBytes[uvIndex];
          final v = vBytes[uvIndex];
          
          // Process 2x2 block
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

  /// Helper to set YUV pixel efficiently
  void _setYUVPixel(img.Image image, int x, int y, Uint8List yBytes, int yRowStride, 
      int u, int v, int width, int height) {
    if (x < width && y < height) {
      final yIndex = y * yRowStride + x;
      final yp = yBytes[yIndex];
      
      // Fast YUV to RGB conversion constants
      final c = yp - 16;
      final d = u - 128;
      final e = v - 128;
      
      int r = ((298 * c + 409 * e + 128) >> 8).clamp(0, 255);
      int g = ((298 * c - 100 * d - 208 * e + 128) >> 8).clamp(0, 255);
      int b = ((298 * c + 516 * d + 128) >> 8).clamp(0, 255);
      
      image.setPixelRgb(x, y, r, g, b);
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
}
