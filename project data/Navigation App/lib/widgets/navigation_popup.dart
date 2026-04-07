import 'package:flutter/material.dart';
import '../models/detection_model.dart';
import '../services/detection_service.dart';

/// Popup widget for navigation alerts with enhanced visibility and door interaction
class NavigationPopupWidget extends StatefulWidget {
  final NavigationPopup? popup;
  final Function(String)? onDoorResponse;  // Callback for door responses

  const NavigationPopupWidget({
    Key? key,
    required this.popup,
    this.onDoorResponse,
  }) : super(key: key);

  @override
  State<NavigationPopupWidget> createState() => _NavigationPopupWidgetState();
}

class _NavigationPopupWidgetState extends State<NavigationPopupWidget>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late Animation<double> _scaleAnimation;
  bool _isHandlingResponse = false;

  @override
  void initState() {
    super.initState();
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _scaleController, curve: Curves.elasticOut),
    );
    _scaleController.forward();
  }

  @override
  void didUpdateWidget(NavigationPopupWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.popup != widget.popup && widget.popup != null) {
      _scaleController.reset();
      _scaleController.forward();
      _isHandlingResponse = false;
    }
  }

  @override
  void dispose() {
    _scaleController.dispose();
    super.dispose();
  }

  /// Handle door response (Yes/No)
  Future<void> _handleDoorResponse(String response) async {
    if (_isHandlingResponse) return;

    setState(() {
      _isHandlingResponse = true;
    });

    try {
      final detectionService = DetectionService();
      final messageWords = (widget.popup?.message ?? '').split(' ').where((w) => w.isNotEmpty).toList();
      final doorClass = messageWords.length > 1 ? messageWords[1] : 'Door';
      final doorDistance = widget.popup?.distance ?? 0.0;

      // Send response to backend
      final result = await detectionService.handleDoorResponse(
        userResponse: response,
        doorClass: doorClass,
        doorDistance: doorDistance,
      );

      if (result != null && mounted) {
        print('\n🎯 Door Response Handled:');
        print('  Action: ${result['action']}');
        print('  Direction: ${result['navigation']?['direction'] ?? "N/A"}');
        print('  Message: ${result['message']}');

        // Call callback if provided
        widget.onDoorResponse?.call(response);

        // Show feedback
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result['message'] ?? "Request processed"),
              duration: const Duration(seconds: 2),
              backgroundColor: response.toLowerCase() == 'yes' ? Colors.green : Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      print('❌ Error handling door response: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Error processing response'),
            duration: Duration(seconds: 2),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isHandlingResponse = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.popup == null) {
      return const SizedBox.shrink();
    }

    Color backgroundColor;
    IconData iconData;
    Color accentColor;

    switch (widget.popup!.type.toLowerCase()) {
      case 'door':
        backgroundColor = Colors.blue.shade700;
        iconData = Icons.door_front_door;
        accentColor = Colors.cyan;
        break;
      case 'human':
        backgroundColor = Colors.purple;
        iconData = Icons.people;
        accentColor = Colors.cyanAccent;
        break;
      default:
        backgroundColor = Colors.grey;
        iconData = Icons.info;
        accentColor = Colors.blueGrey;
    }

    return ScaleTransition(
      scale: _scaleAnimation,
      child: Center(
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 20),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: backgroundColor.withOpacity(0.95),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: accentColor,
              width: 3,
            ),
            boxShadow: [
              BoxShadow(
                color: accentColor.withOpacity(0.8),
                blurRadius: 25,
                spreadRadius: 5,
              ),
              BoxShadow(
                color: Colors.black.withOpacity(0.5),
                blurRadius: 15,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Icon with pulse effect
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white,
                    width: 2,
                  ),
                ),
                child: Icon(
                  iconData,
                  size: 35,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 10),

              // Type (DOOR/HUMAN)
              Text(
                widget.popup!.type.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 8),

              // Message
              Text(
                widget.popup!.message,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),

              // Question (for door popups)
              if (widget.popup!.question != null) ...[
                Text(
                  widget.popup!.question!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 9,
                    fontWeight: FontWeight.w500,
                    fontStyle: FontStyle.italic,
                  ),
                ),
                const SizedBox(height: 8),
              ],

              // Distance with emphasis
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.white70,
                    width: 1.5,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.straighten,
                      color: Colors.white,
                      size: 12,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'Distance: ${widget.popup!.distance.toStringAsFixed(1)}m',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),

              // Yes/No buttons for door popups
              if (widget.popup!.type.toLowerCase() == 'door' && widget.popup!.options != null) ...[
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    // Yes Button
                    ElevatedButton.icon(
                      onPressed: _isHandlingResponse ? null : () => _handleDoorResponse('Yes'),
                      icon: const Icon(Icons.check),
                      label: const Text('Yes'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        disabledBackgroundColor: Colors.grey,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                    // No Button
                    ElevatedButton.icon(
                      onPressed: _isHandlingResponse ? null : () => _handleDoorResponse('No'),
                      icon: const Icon(Icons.close),
                      label: const Text('No'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        disabledBackgroundColor: Colors.grey,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
