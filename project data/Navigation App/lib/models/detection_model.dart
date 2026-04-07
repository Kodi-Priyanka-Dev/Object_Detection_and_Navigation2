/// Detection Model
/// Represents a detected object from the backend
class Detection {
  final String className;
  final double confidence;
  final Position position;
  final double distance;
  final int width;
  final int height;

  Detection({
    required this.className,
    required this.confidence,
    required this.position,
    required this.distance,
    required this.width,
    required this.height,
  });

  factory Detection.fromJson(Map<String, dynamic> json) {
    return Detection(
      className: json['class'] ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      position: Position.fromJson(json['position'] ?? {}),
      distance: (json['distance'] as num?)?.toDouble() ?? 0.0,
      width: (json['width'] as num?)?.toInt() ?? 0,
      height: (json['height'] as num?)?.toInt() ?? 0,
    );
  }
}

/// Position of detected object
class Position {
  final double x;
  final double y;
  final double x1;
  final double y1;
  final double x2;
  final double y2;
  final double centerX;
  final double centerY;

  Position({
    required this.x,
    required this.y,
    required this.x1,
    required this.y1,
    required this.x2,
    required this.y2,
    required this.centerX,
    required this.centerY,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      x: (json['x'] as num?)?.toDouble() ?? 0.0,
      y: (json['y'] as num?)?.toDouble() ?? 0.0,
      x1: (json['x1'] as num?)?.toDouble() ?? 0.0,
      y1: (json['y1'] as num?)?.toDouble() ?? 0.0,
      x2: (json['x2'] as num?)?.toDouble() ?? 0.0,
      y2: (json['y2'] as num?)?.toDouble() ?? 0.0,
      centerX: (json['center_x'] as num?)?.toDouble() ?? 0.0,
      centerY: (json['center_y'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// Navigation instructions
class Navigation {
  final String direction;
  final String? arrow;
  final String? message;
  final NavigationPopup? popup;

  Navigation({
    required this.direction,
    this.arrow,
    this.message,
    this.popup,
  });

  factory Navigation.fromJson(Map<String, dynamic> json) {
    return Navigation(
      direction: json['direction'] ?? 'STRAIGHT',
      arrow: json['arrow'],
      message: json['message'],
      popup: json['popup'] != null 
          ? NavigationPopup.fromJson(json['popup']) 
          : null,
    );
  }
}

/// Navigation popup information
class NavigationPopup {
  final String type;
  final String message;
  final String? question;  // For door popups: "Do you want to go through this door?"
  final double distance;
  final double? confidence;  // Door detection confidence
  final Position? position;
  final List<String>? options;  // e.g., ["Yes", "No"]
  final String? actionUrl;  // Backend endpoint to handle response

  NavigationPopup({
    required this.type,
    required this.message,
    this.question,
    required this.distance,
    this.confidence,
    this.position,
    this.options,
    this.actionUrl,
  });

  factory NavigationPopup.fromJson(Map<String, dynamic> json) {
    return NavigationPopup(
      type: json['type'] ?? '',
      message: json['message'] ?? '',
      question: json['question'],
      distance: (json['distance'] ?? 0).toDouble(),
      confidence: json['confidence'] != null ? (json['confidence'] as num).toDouble() : null,
      position: json['position'] != null 
          ? Position.fromJson(json['position']) 
          : null,
      options: json['options'] != null ? List<String>.from(json['options']) : null,
      actionUrl: json['action_url'],
    );
  }
}

/// Detection Response from backend
class DetectionResponse {
  final bool success;
  final List<Detection> detections;
  final Navigation navigation;
  final FrameSize frameSize;

  DetectionResponse({
    required this.success,
    required this.detections,
    required this.navigation,
    required this.frameSize,
  });

  factory DetectionResponse.fromJson(Map<String, dynamic> json) {
    return DetectionResponse(
      success: json['success'] ?? false,
      detections: (json['detections'] as List?)
              ?.map((d) => Detection.fromJson(d))
              .toList() ??
          [],
      navigation: Navigation.fromJson(json['navigation'] ?? {}),
      frameSize: FrameSize.fromJson(json['frame_size'] ?? {}),
    );
  }
}

/// Frame size information
class FrameSize {
  final int width;
  final int height;

  FrameSize({
    required this.width,
    required this.height,
  });

  factory FrameSize.fromJson(Map<String, dynamic> json) {
    return FrameSize(
      width: (json['width'] as num?)?.toInt() ?? 0,
      height: (json['height'] as num?)?.toInt() ?? 0,
    );
  }
}
