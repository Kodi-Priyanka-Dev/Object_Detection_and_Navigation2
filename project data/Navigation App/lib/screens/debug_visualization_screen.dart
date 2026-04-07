import 'package:flutter/material.dart';
import '../services/detection_service.dart';

class DebugVisualizationScreen extends StatefulWidget {
  @override
  State<DebugVisualizationScreen> createState() =>
      _DebugVisualizationScreenState();
}

class _DebugVisualizationScreenState extends State<DebugVisualizationScreen> {
  bool _isConnected = false;
  bool _showInfo = true;
  String _connectionStatus = 'Connecting...';
  final _detectionService = DetectionService();

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    try {
      final ok = await _detectionService.healthCheck();
      
      if (mounted) {
        setState(() {
          _isConnected = ok != null && ok['status'] == 'healthy';
          _connectionStatus = _isConnected
              ? 'Backend Connected @ ${DetectionService.baseUrl.replaceFirst('http://', '')}'
              : 'Backend Offline @ ${DetectionService.baseUrl.replaceFirst('http://', '')}';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isConnected = false;
          _connectionStatus = 'Connection Failed: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Debug Visualization'),
        backgroundColor: Colors.black87,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.info),
            onPressed: () {
              setState(() => _showInfo = !_showInfo);
            },
          ),
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _checkConnection,
          ),
        ],
      ),
      body: Column(
        children: [
          // Connection Status Bar
          Container(
            padding: EdgeInsets.all(12),
            color: _isConnected ? Colors.green[900] : Colors.red[900],
            child: Row(
              children: [
                Icon(
                  _isConnected ? Icons.check_circle : Icons.cancel,
                  color: Colors.white,
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _connectionStatus,
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                ),
              ],
            ),
          ),
          // Video Stream
          Expanded(
            child: _isConnected
                ? _buildVideoStream()
                : _buildConnectionError(),
          ),
          // Info Panel
          if (_showInfo) _buildInfoPanel(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pop(context),
        tooltip: 'Close Debug Panel',
        child: Icon(Icons.close),
      ),
    );
  }

  Widget _buildVideoStream() {
    final videoStreamUrl = '${DetectionService.baseUrl}/video_feed';

    return Container(
      color: Colors.black,
      child: Stack(
        children: [
          // Video Stream Image
          Center(
            child: Image.network(
              videoStreamUrl,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) {
                return Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.videocam_off, size: 64, color: Colors.white54),
                    SizedBox(height: 16),
                    Text(
                      'Stream Unavailable\nMake sure camera is connected\nand backend is running',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white54),
                    ),
                  ],
                );
              },
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Center(
                  child: CircularProgressIndicator(
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded /
                            loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                );
              },
            ),
          ),
          // Overlay Info
          Positioned(
            top: 16,
            left: 16,
            right: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '🎥 Live Visualization',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '📍 Device: NVIDIA RTX A2000 (cuda:0)',
                        style: TextStyle(color: Colors.cyan, fontSize: 12),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '🔴 Red Arrow = Door Direction',
                        style: TextStyle(color: Colors.red, fontSize: 32),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '👤 Yellow Circle = User Position',
                        style: TextStyle(color: Colors.yellow, fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectionError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.cloud_off, size: 80, color: Colors.red),
          SizedBox(height: 16),
          Text(
            'Backend Connection Failed',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text(
            'Ensure backend_service.py is running',
            style: TextStyle(fontSize: 14, color: Colors.grey),
          ),
          SizedBox(height: 16),
          ElevatedButton(
            onPressed: _checkConnection,
            child: Text('Retry Connection'),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoPanel() {
    return Container(
      color: Colors.grey[900],
      padding: EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '📊 Debug Information',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          SizedBox(height: 8),
          Text(
            '🟠 Orange Box = Door Detected',
            style: TextStyle(color: Colors.orange, fontSize: 12),
          ),
          Text(
            '🟢 Green Box = Other Objects',
            style: TextStyle(color: Colors.greenAccent, fontSize: 12),
          ),
          Text(
            '📏 Distance displayed in meters',
            style: TextStyle(color: Colors.lightBlue, fontSize: 12),
          ),
          Text(
            '⏱️  Real-time GPU acceleration enabled',
            style: TextStyle(color: Colors.cyan, fontSize: 12),
          ),
        ],
      ),
    );
  }
}
