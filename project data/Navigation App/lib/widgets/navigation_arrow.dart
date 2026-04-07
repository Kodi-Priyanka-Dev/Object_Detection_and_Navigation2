import 'package:flutter/material.dart';
import '../models/detection_model.dart';

/// Arrow widget that shows navigation direction near doors
/// Arrow displays as long as door is detected
class NavigationArrow extends StatelessWidget {
  final String? direction;
  final Detection? doorDetection; // Door detection object for positioning arrow near door
  final Size? screenSize; // Screen size for position calculations

  const NavigationArrow({
    Key? key,
    required this.direction,
    this.doorDetection,
    this.screenSize,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (direction == null) {
      return const SizedBox.shrink();
    }

    IconData iconData;
    Color color;
    String label;
    
    switch (direction!.toUpperCase()) {
      case 'LEFT':
        iconData = Icons.arrow_back;
        color = Colors.purpleAccent;
        label = 'MOVE LEFT';
        break;
      case 'RIGHT':
        iconData = Icons.arrow_forward;
        color = Colors.purpleAccent;
        label = 'MOVE RIGHT';
        break;
      case 'FORWARD':
        iconData = Icons.arrow_upward;
        color = Colors.greenAccent;
        label = 'GO THROUGH';
        break;
      default:
        return const SizedBox.shrink();
    }

    // If door is detected, position arrow near the door
    if (doorDetection != null && screenSize != null &&
        screenSize!.width > 0 && screenSize!.height > 0) {
      final screenWidth = MediaQuery.of(context).size.width;
      final screenHeight = MediaQuery.of(context).size.height;
      
      final xPos = (doorDetection!.position.centerX / screenSize!.width) * screenWidth;
      final yPos = (doorDetection!.position.centerY / screenSize!.height) * screenHeight;
      
      // Verify coordinates are valid (not NaN or Infinity)
      if (!xPos.isFinite || !yPos.isFinite) {
        return const SizedBox.shrink();
      }

      return Stack(
        children: [
          // Main arrow symbol - COMPACT
          Positioned(
            left: xPos - 30,
            top: yPos - 40,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.85),
                shape: BoxShape.circle,
                border: Border.all(color: color, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: color.withOpacity(0.8),
                    blurRadius: 20,
                    spreadRadius: 3,
                  ),
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 10,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: Icon(
                iconData,
                size: 35,
                color: color,
              ),
            ),
          ),
          
          // Text label below arrow
          Positioned(
            left: xPos - 25,
            top: yPos + 10,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: color.withOpacity(0.9),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: color, width: 1.5),
              ),
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 9,
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ],
      );
    }

    // Default fallback - show at bottom center if no door detected
    return Positioned(
      bottom: 60,
      left: MediaQuery.of(context).size.width / 2 - 30,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Glow effect rings
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: color.withOpacity(0.3), width: 1),
            ),
          ),
          Container(
            width: 55,
            height: 55,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: color.withOpacity(0.5), width: 1),
            ),
          ),
          
          // Main circle with arrow
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.7),
              shape: BoxShape.circle,
              border: Border.all(color: color, width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(0.6),
                  blurRadius: 15,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Icon(
              iconData,
              size: 35,
              color: color,
            ),
          ),
          
          // Text label below
          Positioned(
            bottom: -25,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: color.withOpacity(0.9),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 9,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
