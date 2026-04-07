import 'dart:async';
import 'dart:math' as math;
import 'package:sensors_plus/sensors_plus.dart';

/// Navigation direction enum
enum NavDirection { left, right, forward, none }

/// Calibration state
enum CalibrationState { notStarted, inProgress, done }

/// Sensor fusion result
class NavigationState {
  final NavDirection direction;
  final double heading;        // 0–360° magnetic heading
  final double tiltAngle;      // phone tilt in degrees
  final double confidence;     // 0.0–1.0
  final String debugLabel;

  const NavigationState({
    required this.direction,
    required this.heading,
    required this.tiltAngle,
    required this.confidence,
    required this.debugLabel,
  });
}

/// Fuses magnetometer + accelerometer + gyroscope to produce navigation directions.
/// Call [setTargetHeading] once you know where the user needs to go.
/// Subscribe to [stream] for real-time [NavigationState] updates.
class SensorNavigationService {
  // ── Streams ────────────────────────────────────────────────────────────────
  StreamSubscription? _magSub;
  StreamSubscription? _accelSub;
  StreamSubscription? _gyroSub;

  final _controller = StreamController<NavigationState>.broadcast();
  Stream<NavigationState> get stream => _controller.stream;

  // ── Raw sensor values ──────────────────────────────────────────────────────
  double _magX = 0, _magY = 0, _magZ = 0;
  double _accelX = 0, _accelY = 0, _accelZ = 9.8;
  double _gyroZ = 0;

  // ── Calibration offset ─────────────────────────────────────────────────────
  double _headingOffset = 0;
  CalibrationState _calibState = CalibrationState.notStarted;
  CalibrationState get calibrationState => _calibState;

  // ── Target ─────────────────────────────────────────────────────────────────
  double? _targetHeading; // degrees 0–360

  // ── Smoothing ──────────────────────────────────────────────────────────────
  final List<double> _headingBuffer = [];
  static const int _bufSize = 4;  // REDUCED from 8 for faster response
  double _gyroHeadingDrift = 0;   // Accumulated gyroscope drift correction
  double _lastHeading = 0;
  DateTime? _lastGyroTime;

  // ── Thresholds ─────────────────────────────────────────────────────────────
  static const double _leftRightThreshold = 25.0;  // degrees off-target → show L/R
  static const double _forwardThreshold   = 25.0;  // degrees ± → show Forward
  static const double _tiltWarnAngle      = 75.0;  // INCREASED from 60 for more tolerance

  // ── Start / Stop ───────────────────────────────────────────────────────────
  void start() {
    _magSub = magnetometerEventStream().listen(_onMag);
    _accelSub = accelerometerEventStream().listen(_onAccel);
    _gyroSub = gyroscopeEventStream().listen(_onGyro);
    print('🧭 Sensor Navigation Service started');
  }

  void stop() {
    _magSub?.cancel();
    _accelSub?.cancel();
    _gyroSub?.cancel();
    _controller.close();
    print('🧭 Sensor Navigation Service stopped');
  }

  // ── Sensor callbacks ───────────────────────────────────────────────────────
  void _onMag(MagnetometerEvent e) {
    _magX = e.x; _magY = e.y; _magZ = e.z;
    _compute();
  }

  void _onAccel(AccelerometerEvent e) {
    _accelX = e.x; _accelY = e.y; _accelZ = e.z;
  }

  void _onGyro(GyroscopeEvent e) {
    _gyroZ = e.z;
    
    // Use gyroscope for heading drift correction
    if (_lastGyroTime != null) {
      final now = DateTime.now();
      final dt = now.difference(_lastGyroTime!).inMilliseconds / 1000.0;
      if (dt > 0 && dt < 0.1) {  // Only apply if reasonable time delta
        // Z-axis rotation affects heading
        final dHeading = (_gyroZ * dt * 180 / math.pi);
        _gyroHeadingDrift += dHeading;
      }
    }
    _lastGyroTime = DateTime.now();
  }

  // ── Core fusion ────────────────────────────────────────────────────────────
  void _compute() {
    // 1. Tilt-compensated heading from mag + accel
    final double ax = _accelX, ay = _accelY, az = _accelZ;
    final double norm = math.sqrt(ax * ax + ay * ay + az * az);
    if (norm < 0.001) return;

    final double roll  = math.atan2(ay, az);
    final double pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az));

    final double mx = _magX * math.cos(pitch) +
        _magZ * math.sin(pitch);
    final double my = _magX * math.sin(roll) * math.sin(pitch) +
        _magY * math.cos(roll) -
        _magZ * math.sin(roll) * math.cos(pitch);

    double heading = math.atan2(-my, mx) * (180 / math.pi);
    if (heading < 0) heading += 360;

    // 2. Apply calibration offset AND gyroscope drift correction
    heading = (heading - _headingOffset + 360) % 360;
    // Apply minimal gyro drift (gyro tends to accumulate error, so use it gently)
    heading = (heading + _gyroHeadingDrift * 0.05) % 360;  // Only 5% gyro influence
    _lastHeading = heading;

    // 3. Smooth heading with circular buffer for stability
    _headingBuffer.add(heading);
    if (_headingBuffer.length > _bufSize) _headingBuffer.removeAt(0);
    final double smoothed = _circularMean(_headingBuffer);

    // 4. Tilt angle of the phone (but with LESS penalty)
    final double tilt = math.atan2(math.sqrt(ax * ax + ay * ay), az.abs()) * (180 / math.pi);
    final double confidence = tilt > _tiltWarnAngle ? 0.6 : 1.0;  // REDUCED penalty from 0.3 to 0.6

    // 5. Determine direction vs target
    NavDirection dir = NavDirection.none;
    String label = 'No target set';

    if (_targetHeading != null) {
      double diff = (smoothed - _targetHeading! + 360) % 360;
      if (diff > 180) diff -= 360; // -180 to +180

      if (diff.abs() <= _forwardThreshold) {
        dir = NavDirection.forward;
        label = 'Go Straight (${diff.toStringAsFixed(1)}°)';
      } else if (diff > _leftRightThreshold) {
        dir = NavDirection.right;
        label = 'Turn Right (${diff.toStringAsFixed(1)}°)';
      } else if (diff < -_leftRightThreshold) {
        dir = NavDirection.left;
        label = 'Turn Left (${diff.abs().toStringAsFixed(1)}°)';
      } else {
        dir = NavDirection.forward;
        label = 'Almost there (${diff.toStringAsFixed(1)}°)';
      }
    }

    if (!_controller.isClosed) {
      _controller.add(NavigationState(
        direction: dir,
        heading: smoothed,
        tiltAngle: tilt,
        confidence: confidence,
        debugLabel: label,
      ));
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Set the heading (0–360°) the user should walk toward.
  void setTargetHeading(double degrees) {
    _targetHeading = degrees % 360;
    print('🧭 Target heading set to: ${_targetHeading?.toStringAsFixed(1)}°');
  }

  /// Calibrate: capture current heading as "forward" reference.
  /// Call when the user is facing the desired direction.
  Future<void> calibrate() async {
    _calibState = CalibrationState.inProgress;
    print('🧭 Calibration in progress...');
    await Future.delayed(const Duration(milliseconds: 500));
    // Capture mean of last readings as offset
    if (_headingBuffer.isNotEmpty) {
      _headingOffset = (_headingOffset + _circularMean(_headingBuffer)) % 360;
      print('🧭 Calibration complete. Offset: ${_headingOffset.toStringAsFixed(1)}°');
    }
    _calibState = CalibrationState.done;
  }

  /// Get current calibration state
  CalibrationState get currentCalibrationState => _calibState;

  /// Reset calibration to start over
  void resetCalibration() {
    _headingOffset = 0;
    _calibState = CalibrationState.notStarted;
    _headingBuffer.clear();
    _gyroHeadingDrift = 0;  // RESET gyro drift on calibration
    _lastGyroTime = null;
    print('🧭 Calibration reset (including gyro drift)');
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  double _circularMean(List<double> angles) {
    double sinSum = 0, cosSum = 0;
    for (final a in angles) {
      final r = a * math.pi / 180;
      sinSum += math.sin(r);
      cosSum += math.cos(r);
    }
    double mean = math.atan2(sinSum, cosSum) * 180 / math.pi;
    if (mean < 0) mean += 360;
    return mean;
  }

  /// Get current magnetic heading (0–360°)
  double getCurrentHeading() {
    return _headingBuffer.isNotEmpty ? _circularMean(_headingBuffer) : 0;
  }

  /// Dispose resources
  void dispose() {
    stop();
  }
}
