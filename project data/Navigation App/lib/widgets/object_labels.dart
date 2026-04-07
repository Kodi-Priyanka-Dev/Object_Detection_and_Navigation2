import 'package:flutter/material.dart';
import '../models/detection_model.dart';

/// Widget to display detected object labels (NO bounding boxes)
class ObjectLabels extends StatelessWidget {
  final List<Detection> detections;
  final Size screenSize;

  const ObjectLabels({
    Key? key,
    required this.detections,
    required this.screenSize,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: detections.map((detection) {
        // Calculate position on screen (proportional to camera frame)
        // Add safety check to prevent NaN from division by zero
        if (screenSize.width <= 0 || screenSize.height <= 0) {
          return const SizedBox.shrink();
        }
        
        final xPos = (detection.position.centerX / screenSize.width) * 
                     MediaQuery.of(context).size.width;
        final yPos = (detection.position.centerY / screenSize.height) * 
                     MediaQuery.of(context).size.height;
        
        // Verify coordinates are valid (not NaN or Infinity)
        if (!xPos.isFinite || !yPos.isFinite) {
          return const SizedBox.shrink();
        }

        return Positioned(
          left: xPos - 60, // Centered label
          top: yPos - 20,
          child: _buildLabel(detection),
        );
      }).toList(),
    );
  }

  Widget _buildLabel(Detection detection) {
    // Choose color based on object class
    Color labelColor = _getColorForClass(detection.className);
    Color accentColor = labelColor.withOpacity(0.8);

    return SizedBox(
      width: 120,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
        // Label badge with animation-ready design
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: labelColor.withOpacity(0.90),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: [
              BoxShadow(
                color: accentColor.withOpacity(0.6),
                blurRadius: 12,
                spreadRadius: 2,
              ),
              BoxShadow(
                color: Colors.black.withOpacity(0.4),
                blurRadius: 8,
                spreadRadius: 1,
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Object name - Primary info
              Text(
                detection.className.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: 2),
              
              // Distance - Secondary info
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${detection.distance.toStringAsFixed(1)}m',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              
              // Confidence as small badge
              if (detection.confidence > 0.7)
                Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: Text(
                    '${(detection.confidence * 100).toStringAsFixed(0)}%',
                    style: const TextStyle(
                      color: Colors.white54,
                      fontSize: 9,
                    ),
                  ),
                ),
            ],
          ),
        ),
        
        // Pointer line connecting to object
        const SizedBox(height: 6),
        CustomPaint(
          size: const Size(2, 12),
          painter: _PointerPainter(color: labelColor),
        ),
        ],
      ),
    );
  }

  Color _getColorForClass(String className) {
    final lowerClass = className.toLowerCase();
    
    switch (lowerClass) {
      case 'door':
      case 'glass door':
        return const Color(0xFF00BCD4); // Cyan
      case 'wooden entrance':
        return const Color(0xFFFF9800); // Orange
      case 'human':
      case 'humans':
      case 'person':
        return const Color(0xFFFF5252); // Red
      case 'table':
        return const Color(0xFF9C27B0); // Purple
      case 'sofa':
      case 'couch':
        return const Color(0xFF795548); // Brown
      case 'chair':
      case 'chairs':
        return const Color(0xFF009688); // Teal
      case 'wall':
        return const Color(0xFF4CAF50); // Green
      case 'window':
        return const Color(0xFF2196F3); // Blue
      default:
        return const Color(0xFF757575); // Grey
    }
  }
}

/// Custom painter for the pointer line
class _PointerPainter extends CustomPainter {
  final Color color;

  _PointerPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color.withOpacity(0.6)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      paint,
    );
    
    // Draw arrowhead
    final arrowPaint = Paint()
      ..color = color.withOpacity(0.7)
      ..style = PaintingStyle.fill;

    canvas.drawCircle(
      Offset(size.width / 2, size.height),
      2.5,
      arrowPaint,
    );
  }

  @override
  bool shouldRepaint(_PointerPainter oldDelegate) =>
      oldDelegate.color != color;
}
