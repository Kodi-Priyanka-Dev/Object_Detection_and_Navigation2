import 'package:flutter/material.dart';

class DoorPopupDialog {
  // Door detection popup
  static Future<bool?> showDoorPopup(
    BuildContext context,
    double distance,
  ) async {
    return showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          title: Row(
            children: const [
              Icon(Icons.door_front_door, color: Colors.blue, size: 22),
              SizedBox(width: 8),
              Text(
                'Door Detected',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ],
          ),
          content: Text(
            'Door is detected at ${distance.toStringAsFixed(1)} meters. Do you want to open and go?',
            style: const TextStyle(fontSize: 13),
          ),
          actionsAlignment: MainAxisAlignment.spaceEvenly,
          actions: [
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.grey,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 8,
                ),
              ),
              onPressed: () => Navigator.pop(context, false),
              child: const Text(
                'NO',
                style: TextStyle(fontSize: 14),
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 8,
                ),
              ),
              onPressed: () => Navigator.pop(context, true),
              child: const Text(
                'YES',
                style: TextStyle(fontSize: 14),
              ),
            ),
          ],
        );
      },
    );
  }
}
