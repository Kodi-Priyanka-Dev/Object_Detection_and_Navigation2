import 'package:flutter/material.dart';
import 'dart:math';

class DoorArrowOverlay extends StatelessWidget {
  final Offset position;
  final Size screenSize;
  final double distance;
  
  const DoorArrowOverlay({
    Key? key,
    required this.position,
    required this.screenSize,
    required this.distance,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // User position (bottom center)
    final userX = screenSize.width / 2;
    final userY = screenSize.height - 50;
    
    // Door position
    final doorX = position.dx;
    final doorY = position.dy;

    return CustomPaint(
      painter: ArrowPainter(
        startPoint: Offset(userX, userY),
        endPoint: Offset(doorX, doorY),
        distance: distance,
      ),
      size: screenSize,
    );
  }
}

class ArrowPainter extends CustomPainter {
  final Offset startPoint;
  final Offset endPoint;
  final double distance;

  ArrowPainter({
    required this.startPoint,
    required this.endPoint,
    required this.distance,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Line paint (red)
    final linePaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;

    // Draw line from user to door
    canvas.drawLine(startPoint, endPoint, linePaint);

    // Calculate angle for arrowhead
    final dx = endPoint.dx - startPoint.dx;
    final dy = endPoint.dy - startPoint.dy;
    final angle = atan2(dy, dx);
    
    // Arrow properties
    final arrowSize = 25.0;
    final arrowAngle = pi / 6; // 30 degrees

    // Arrowhead points
    final arrowPoint1 = Offset(
      endPoint.dx - arrowSize * cos(angle - arrowAngle),
      endPoint.dy - arrowSize * sin(angle - arrowAngle),
    );

    final arrowPoint2 = Offset(
      endPoint.dx - arrowSize * cos(angle + arrowAngle),
      endPoint.dy - arrowSize * sin(angle + arrowAngle),
    );

    // Draw arrowhead triangle
    final arrowPath = Path()
      ..moveTo(endPoint.dx, endPoint.dy)
      ..lineTo(arrowPoint1.dx, arrowPoint1.dy)
      ..lineTo(arrowPoint2.dx, arrowPoint2.dy)
      ..close();

    final arrowPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.fill;

    canvas.drawPath(arrowPath, arrowPaint);

    // Distance text at midpoint
    final midX = (startPoint.dx + endPoint.dx) / 2;
    final midY = (startPoint.dy + endPoint.dy) / 2;

    final textSpan = TextSpan(
      text: '${distance.toStringAsFixed(1)} m',
      style: const TextStyle(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );

    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    // Draw background box for text
    final textBgPaint = Paint()
      ..color = Colors.red.withOpacity(0.85)
      ..style = PaintingStyle.fill;

    final textBgRect = Rect.fromLTWH(
      midX - textPainter.width / 2 - 8,
      midY - 35,
      textPainter.width + 16,
      textPainter.height + 8,
    );

    canvas.drawRRect(
      RRect.fromRectAndRadius(textBgRect, Radius.circular(6)),
      textBgPaint,
    );

    // Draw text
    textPainter.paint(
      canvas,
      Offset(midX - textPainter.width / 2, midY - 32),
    );
  }

  @override
  bool shouldRepaint(ArrowPainter oldDelegate) {
    return oldDelegate.endPoint != endPoint ||
        oldDelegate.distance != distance;
  }
}
