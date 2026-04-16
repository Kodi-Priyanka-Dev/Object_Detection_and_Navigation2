import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../services/sensor_navigation_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// SENSOR NAVIGATION HUD
// Drop this anywhere in your widget tree. It self-manages sensor lifecycle.
// ─────────────────────────────────────────────────────────────────────────────

class SensorNavigationHUD extends StatefulWidget {
  /// Heading (0–360°) the user should walk toward. Null = compass-only mode.
  final double? targetHeading;

  /// When false, compass stays visible; turn arrow shows a standby state (no L/R/F).
  final bool showGuidance;

  /// Throttled sensor updates for event-based TTS (heading/tilt) in the parent.
  final void Function(NavigationState state)? onNavigationStateChanged;

  const SensorNavigationHUD({
    Key? key,
    this.targetHeading,
    this.showGuidance = true,
    this.onNavigationStateChanged,
  }) : super(key: key);

  @override
  State<SensorNavigationHUD> createState() => _SensorNavigationHUDState();
}

class _SensorNavigationHUDState extends State<SensorNavigationHUD>
    with TickerProviderStateMixin {
  late final SensorNavigationService _svc;

  // Animation controllers
  late final AnimationController _pulseCtrl;
  late final AnimationController _arrowCtrl;
  late final AnimationController _rotateCtrl;
  late final Animation<double> _pulseAnim;
  late final Animation<double> _arrowAnim;

  NavigationState? _state;
  NavDirection _lastDirection = NavDirection.none;
  double _compassAngle = 0;
  bool _autoTargetLocked = false; // Use initial heading as default target

  @override
  void initState() {
    super.initState();
    _initAnimations();
    _svc = SensorNavigationService();
    if (widget.targetHeading != null) {
      _svc.setTargetHeading(widget.targetHeading!);
    }
    _svc.start();
    _svc.stream.listen(_onState);

    // Ensure the arrow UI is visible immediately (not scaled to 0
    // before the first direction-change animation fires).
    _arrowCtrl.value = 1.0;
  }

  void _initAnimations() {
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _arrowCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _rotateCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );

    _pulseAnim = Tween<double>(begin: 0.92, end: 1.08).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
    _arrowAnim = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _arrowCtrl, curve: Curves.elasticOut),
    );
  }

  void _onState(NavigationState s) {
    if (!mounted) return;

    // Auto-set target heading once when none is provided
    if (!_autoTargetLocked && widget.targetHeading == null) {
      _svc.setTargetHeading(s.heading);
      _autoTargetLocked = true;
    }

    // Throttle UI updates to meaningful changes only
    final prev = _state;
    final bool shouldUpdate = prev == null ||
        (s.heading - prev.heading).abs() > 0.5 ||
        (s.tiltAngle - prev.tiltAngle).abs() > 1.5 ||
        s.direction != prev.direction;

    if (shouldUpdate) {
      setState(() {
        _state = s;
        _compassAngle = s.heading * math.pi / 180;
      });
      widget.onNavigationStateChanged?.call(s);
    }

    if (widget.showGuidance && s.direction != _lastDirection) {
      _lastDirection = s.direction;
      _arrowCtrl.forward(from: 0);
    } else if (!widget.showGuidance) {
      _lastDirection = s.direction;
    }
  }

  @override
  void didUpdateWidget(SensorNavigationHUD old) {
    super.didUpdateWidget(old);
    if (widget.targetHeading != old.targetHeading &&
        widget.targetHeading != null) {
      _svc.setTargetHeading(widget.targetHeading!);
    }
  }

  @override
  void dispose() {
    _svc.stop();
    _pulseCtrl.dispose();
    _arrowCtrl.dispose();
    _rotateCtrl.dispose();
    super.dispose();
  }

  // ── Build ──────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final s = _state;
    if (s == null) return _buildLoading();

    return Container(
      constraints: const BoxConstraints(minHeight: 86),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.82),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.indigo.withOpacity(0.5),
          width: 1.5,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${s.heading.toStringAsFixed(1)}°  ${_cardinalLabel(s.heading)}',
                  style: const TextStyle(
                    color: Colors.cyanAccent,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Center(child: _buildCompassRing(s)),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Center(
              child: widget.showGuidance
                  ? _buildDirectionArrow(s)
                  : _buildGuidanceStandby(),
            ),
          ),
        ],
      ),
    );
  }

  // ── Loading state ──────────────────────────────────────────────────────────
  Widget _buildLoading() {
    return Container(
      height: 86,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.78),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.indigo.withOpacity(0.5),
          width: 1.5,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 14,
            height: 14,
            child: CircularProgressIndicator(
              strokeWidth: 1.5,
              valueColor: AlwaysStoppedAnimation(const Color(0xFF00D4FF)),
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'Init sensors...',
            style: TextStyle(
              color: Color(0xFF00D4FF),
              fontSize: 9,
              letterSpacing: 2,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }

  // ── Header ─────────────────────────────────────────────────────────────────
  Widget _buildHeader(NavigationState s) {
    final cardinalLabel = _cardinalLabel(s.heading);
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 8, 10, 0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Heading readout (compact)
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(
              '${s.heading.toStringAsFixed(1)}°',
              style: const TextStyle(
                color: Color(0xFF00D4FF),
                fontSize: 16,
                fontWeight: FontWeight.w700,
                fontFamily: 'monospace',
                letterSpacing: 1,
              ),
            ),
            Text(
              cardinalLabel,
              style: const TextStyle(
                color: Color(0xFF4A6FA5),
                fontSize: 9,
                letterSpacing: 2,
              ),
            ),
          ]),
          
          // Calibration button
          GestureDetector(
            onTap: () async {
              await _svc.calibrate();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('🧭 Compass calibrated!'),
                    duration: Duration(milliseconds: 800),
                    backgroundColor: Color(0xFF00FF9F),
                  ),
                );
              }
            },
            child: Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF00D4FF).withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                  color: const Color(0xFF00D4FF).withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: const Icon(
                Icons.refresh,
                size: 13,
                color: Color(0xFF00D4FF),
              ),
            ),
          ),
          
          // Confidence badge
          _buildConfidenceBadge(s.confidence),
        ],
      ),
    );
  }

  Widget _buildConfidenceBadge(double conf) {
    final color = conf > 0.7
        ? const Color(0xFF00FF9F)
        : conf > 0.4
            ? const Color(0xFFFFD700)
            : const Color(0xFFFF4560);
    final label = conf > 0.7 ? 'STABLE' : conf > 0.4 ? 'FAIR' : 'UNSTABLE';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        border: Border.all(color: color.withOpacity(0.6), width: 0.8),
        borderRadius: BorderRadius.circular(12),
        color: color.withOpacity(0.08),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5,
            height: 5,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 8,
              letterSpacing: 1,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ── Compass ring ───────────────────────────────────────────────────────────
  Widget _buildCompassRing(NavigationState s) {
    return SizedBox(
      width: 82,
      height: 82,
      child: AnimatedBuilder(
        animation: _pulseAnim,
        builder: (_, __) => CustomPaint(
          painter: _CompassPainter(
            headingRad: _compassAngle,
            targetRad: widget.targetHeading != null
                ? widget.targetHeading! * math.pi / 180
                : null,
            pulseScale: s.direction == NavDirection.forward
                ? _pulseAnim.value
                : 1.0,
          ),
        ),
      ),
    );
  }

  // ── Standby when no nearby obstacle (compass still active) ────────────────
  Widget _buildGuidanceStandby() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white24, width: 1),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.explore_outlined, size: 22, color: Colors.blueGrey.shade300),
          const SizedBox(height: 6),
          Text(
            'Guidance when obstacle is close',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.blueGrey.shade200,
              fontSize: 9,
              fontWeight: FontWeight.w600,
              height: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  // ── Direction arrow ────────────────────────────────────────────────────────
  Widget _buildDirectionArrow(NavigationState s) {
    final cfg = _arrowConfig(s.direction);

    return ScaleTransition(
      scale: _arrowAnim,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 6),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              cfg.color.withOpacity(0.08),
              cfg.color.withOpacity(0.15),
              cfg.color.withOpacity(0.08),
            ],
          ),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: cfg.color.withOpacity(0.4), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: cfg.color.withOpacity(0.2),
              blurRadius: 15,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Column(
          children: [
            // Arrow icon with glow
            Stack(
              alignment: Alignment.center,
              children: [
                if (s.direction != NavDirection.none)
                  AnimatedBuilder(
                    animation: _pulseAnim,
                    builder: (_, __) => Container(
                      width: 34 * _pulseAnim.value,
                      height: 34 * _pulseAnim.value,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: cfg.color.withOpacity(0.2),
                          width: 1.5,
                        ),
                      ),
                    ),
                  ),
                Icon(
                  cfg.icon,
                  size: 24,
                  color: cfg.color,
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              cfg.label,
              style: TextStyle(
                color: cfg.color,
                fontSize: 10,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Info bar ───────────────────────────────────────────────────────────────
  Widget _buildInfoBar(NavigationState s) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 0, 10, 8),
      child: Row(
        children: [
          _infoChip(
            Icons.screen_rotation_outlined,
            'TILT',
            '${s.tiltAngle.toStringAsFixed(0)}°',
            const Color(0xFF4A6FA5),
          ),
          const SizedBox(width: 6),
          if (widget.targetHeading != null)
            Expanded(
              child: _infoChip(
                Icons.my_location_outlined,
                'TGT',
                '${widget.targetHeading!.toStringAsFixed(0)}°',
                const Color(0xFF00D4FF),
              ),
            ),
        ],
      ),
    );
  }

  Widget _infoChip(IconData icon, String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.07),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.2), width: 0.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: color.withOpacity(0.7)),
          const SizedBox(width: 4),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(
                      color: color.withOpacity(0.5),
                      fontSize: 7,
                      letterSpacing: 1)),
              Text(value,
                  style: TextStyle(
                      color: color,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      fontFamily: 'monospace')),
            ],
          ),
        ],
      ),
    );
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  _ArrowConfig _arrowConfig(NavDirection dir) {
    switch (dir) {
      case NavDirection.left:
        return _ArrowConfig(
          icon: Icons.arrow_back_rounded,
          color: const Color(0xFFBB86FC),
          label: 'TURN LEFT',
        );
      case NavDirection.right:
        return _ArrowConfig(
          icon: Icons.arrow_forward_rounded,
          color: const Color(0xFFBB86FC),
          label: 'TURN RIGHT',
        );
      case NavDirection.forward:
        return _ArrowConfig(
          icon: Icons.arrow_upward_rounded,
          color: const Color(0xFF00FF9F),
          label: 'GO STRAIGHT',
        );
      case NavDirection.none:
        return _ArrowConfig(
          icon: Icons.explore_outlined,
          color: const Color(0xFF4A6FA5),
          label: 'SET TARGET',
        );
    }
  }

  String _cardinalLabel(double heading) {
    const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return dirs[((heading + 22.5) / 45).floor() % 8];
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPASS PAINTER
// ─────────────────────────────────────────────────────────────────────────────
class _CompassPainter extends CustomPainter {
  final double headingRad;
  final double? targetRad;
  final double pulseScale;

  _CompassPainter({
    required this.headingRad,
    this.targetRad,
    this.pulseScale = 1.0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final outerR = size.width / 2 - 4;
    final innerR = outerR - 18;

    // ── Outer ring ─────────────────────────────────────────────────────────
    canvas.drawCircle(
      Offset(cx, cy),
      outerR,
      Paint()
        ..color = const Color(0xFF1A2744).withOpacity(0.10)
        ..style = PaintingStyle.fill,
    );
    canvas.drawCircle(
      Offset(cx, cy),
      outerR,
      Paint()
        ..color = const Color(0xFF00D4FF).withOpacity(0.18)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );

    // ── Tick marks ──────────────────────────────────────────────────────────
    final tickPaint = Paint()
      ..color = const Color(0xFF2A4070)
      ..strokeWidth = 1;
    final majorTickPaint = Paint()
      ..color = const Color(0xFF00D4FF).withOpacity(0.5)
      ..strokeWidth = 1.5;

    for (int i = 0; i < 36; i++) {
      final angle = i * 10 * math.pi / 180;
      final isMajor = i % 9 == 0;
      final tickLen = isMajor ? 14.0 : 7.0;
      final r1 = outerR - 2;
      final r2 = r1 - tickLen;
      canvas.drawLine(
        Offset(cx + r1 * math.sin(angle), cy - r1 * math.cos(angle)),
        Offset(cx + r2 * math.sin(angle), cy - r2 * math.cos(angle)),
        isMajor ? majorTickPaint : tickPaint,
      );
    }

    // ── Target bearing arc ──────────────────────────────────────────────────
    if (targetRad != null) {
      final arcPaint = Paint()
        ..color = const Color(0xFF00FF9F).withOpacity(0.25)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 6
        ..strokeCap = StrokeCap.round;
      final startAngle = targetRad! - math.pi / 2 - 0.3;
      canvas.drawArc(
        Rect.fromCircle(center: Offset(cx, cy), radius: innerR + 4),
        startAngle,
        0.6,
        false,
        arcPaint,
      );
    }

    // ── Heading needle ──────────────────────────────────────────────────────
    final needleLen = innerR - 12;
    final needleTip = Offset(
      cx + needleLen * math.sin(headingRad),
      cy - needleLen * math.cos(headingRad),
    );
    final needleTail = Offset(
      cx - (needleLen * 0.35) * math.sin(headingRad),
      cy + (needleLen * 0.35) * math.cos(headingRad),
    );

    // Glow
    canvas.drawLine(
      needleTail,
      needleTip,
      Paint()
        ..color = const Color(0xFF00D4FF).withOpacity(0.3)
        ..strokeWidth = 8
        ..strokeCap = StrokeCap.round,
    );
    // Needle
    canvas.drawLine(
      needleTail,
      needleTip,
      Paint()
        ..color = const Color(0xFF00D4FF)
        ..strokeWidth = 2.5
        ..strokeCap = StrokeCap.round,
    );

    // ── Target needle ────────────────────────────────────────────────────────
    if (targetRad != null) {
      final tLen = innerR - 20;
      final tTip = Offset(
        cx + tLen * math.sin(targetRad!),
        cy - tLen * math.cos(targetRad!),
      );
      canvas.drawLine(
        Offset(cx, cy),
        tTip,
        Paint()
          ..color = const Color(0xFF00FF9F).withOpacity(0.7)
          ..strokeWidth = 2
          ..strokeCap = StrokeCap.round
          ..style = PaintingStyle.stroke,
      );
    }

    // ── Center dot ──────────────────────────────────────────────────────────
    canvas.drawCircle(
      Offset(cx, cy),
      5 * pulseScale,
      Paint()..color = const Color(0xFF00D4FF),
    );
    canvas.drawCircle(
      Offset(cx, cy),
      3,
      Paint()..color = Colors.white,
    );

    // ── Cardinal labels ──────────────────────────────────────────────────────
    _drawCardinal(canvas, 'N', cx, cy - outerR + 10, const Color(0xFFFF4560));
    _drawCardinal(canvas, 'S', cx, cy + outerR - 8,  const Color(0xFF4A6FA5));
    _drawCardinal(canvas, 'E', cx + outerR - 10, cy, const Color(0xFF4A6FA5));
    _drawCardinal(canvas, 'W', cx - outerR + 10, cy, const Color(0xFF4A6FA5));
  }

  void _drawCardinal(Canvas canvas, String text, double x, double y, Color color) {
    final tp = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w800,
          letterSpacing: 1,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
  }

  @override
  bool shouldRepaint(_CompassPainter old) =>
      old.headingRad != headingRad ||
      old.targetRad != targetRad ||
      old.pulseScale != pulseScale;
}

// ── Internal config helper ──────────────────────────────────────────────────
class _ArrowConfig {
  final IconData icon;
  final Color color;
  final String label;
  const _ArrowConfig({required this.icon, required this.color, required this.label});
}
