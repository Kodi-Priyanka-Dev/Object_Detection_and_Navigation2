import 'package:flutter/material.dart';
import '../models/detection_model.dart';

/// Door Detection Alert Dialog - Compact alert for human/object detection
class DoorDetectionAlert extends StatefulWidget {
  final DetectionResponse detection;

  const DoorDetectionAlert({
    Key? key,
    required this.detection,
  }) : super(key: key);

  @override
  State<DoorDetectionAlert> createState() => _DoorDetectionAlertState();
}

class _DoorDetectionAlertState extends State<DoorDetectionAlert>
    with SingleTickerProviderStateMixin {
  late AnimationController _slideController;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _slideController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, -0.2),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _slideController, curve: Curves.easeOut));
    _slideController.forward();
  }

  @override
  void dispose() {
    _slideController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.detection.detections.isEmpty) {
      return const SizedBox.shrink();
    }

    // Find non-door objects (human, etc.)
    final otherDetections = widget.detection.detections
        .where((d) => !d.className.toLowerCase().contains('door'))
        .toList();

    if (otherDetections.isEmpty) {
      return const SizedBox.shrink();
    }

    // Prefer "human" over generic "person" so person isn't treated as highest priority.
    otherDetections.sort((a, b) {
      final aLower = a.className.toLowerCase();
      final bLower = b.className.toLowerCase();

      int priority(String lower) {
        if (lower == 'human' || lower == 'humans') return 0;
        if (lower == 'person') return 1;
        return 2;
      }

      return priority(aLower).compareTo(priority(bLower));
    });

    final detection = otherDetections.first;
    final nav = widget.detection.navigation;
    final displayName = _getDisplayLabel(detection.className);

    // Determine color based on object type
    Color alertColor;
    IconData icon;
    switch (detection.className.toLowerCase()) {
      case 'human':
        alertColor = const Color(0xFF8EDCFF); // light cyan
        icon = Icons.person;
        break;
      case 'person':
        alertColor = const Color(0xFF8EDCFF); // light cyan
        icon = Icons.people;
        break;
      default:
        alertColor = Colors.orange;
        icon = Icons.warning_rounded;
    }

    // IMPORTANT: Positioned must be a direct child of Stack.
    // Wrap the animated content INSIDE Positioned, not the other way around.
    return Positioned(
      top: 50, // Very close to backend status
      left: 10,
      right: 10,
      child: SlideTransition(
        position: _slideAnimation,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.80),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: alertColor.withOpacity(0.5),
              width: 0.9,
            ),
            boxShadow: [
              BoxShadow(
                color: alertColor.withOpacity(0.2),
                blurRadius: 6,
                spreadRadius: 0,
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Icon
              Container(
                padding: const EdgeInsets.all(1.8),
                decoration: BoxDecoration(
                  color: alertColor.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(5),
                ),
                child: Icon(
                  icon,
                  size: 10,
                  color: alertColor,
                ),
              ),
              const SizedBox(width: 5),

              // Content
              Expanded(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Title
                    Text(
                      '${displayName.toUpperCase()} · ${detection.distance.toStringAsFixed(1)}m',
                      style: TextStyle(
                        color: alertColor,
                        fontSize: 8,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.3,
                      ),
                    ),
                    if (nav.message != null)
                      Text(
                        nav.message ?? '',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 6.5,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getDisplayLabel(String className) {
    final lower = className.toLowerCase();
    if (lower == 'dining table') return 'Table';
    return className;
  }
}
