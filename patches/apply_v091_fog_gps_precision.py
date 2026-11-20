from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"

# 1) Extend the fog composite beyond the viewport diagonal so rotation cannot
# expose the rectangular saveLayer boundary at the top/bottom corners.
fog = pkg / "FogOverlay.kt"
f = fog.read_text(encoding="utf-8")
if "val overscan = kotlin.math.hypot" in f:
    raise SystemExit("v0.9.1 fog overscan patch already applied")
old = """        val layer = canvas.saveLayer(0f, 0f, width.toFloat(), height.toFloat(), null)
        canvas.drawColor(fogColor)
"""
new = """        // The map canvas rotates around its center. Cover the full diagonal of
        // the viewport so the fog layer still reaches every corner at any angle.
        val overscan = kotlin.math.hypot(width.toDouble(), height.toDouble()).toFloat() / 2f + 8f
        val layer = canvas.saveLayer(
            -overscan, -overscan,
            width.toFloat() + overscan, height.toFloat() + overscan,
            null
        )
        val fogFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = fogColor
            style = Paint.Style.FILL
        }
        canvas.drawRect(
            -overscan, -overscan,
            width.toFloat() + overscan, height.toFloat() + overscan,
            fogFill
        )
"""
if old not in f:
    raise SystemExit("v0.9.0 bounded fog layer block not found")
f = f.replace(old, new, 1)
fog.write_text(f, encoding="utf-8")

# 2) Tighten accepted GPS quality and use slightly denser pedestrian sampling.
math_file = pkg / "TrackMath.kt"
m = math_file.read_text(encoding="utf-8")
old_accuracy = "accuracyMeters <= 20f"
if old_accuracy not in m:
    raise SystemExit("GPS accuracy threshold anchor not found")
m = m.replace(old_accuracy, "accuracyMeters <= 12f", 1)
math_file.write_text(m, encoding="utf-8")

service = pkg / "LocationTrackingService.kt"
s = service.read_text(encoding="utf-8")
for old_value, new_value in [
    ("val interval = if (fast) 5_000L else 15_000L", "val interval = if (fast) 3_000L else 7_000L"),
    ("val minInterval = if (fast) 3_000L else 12_000L", "val minInterval = if (fast) 1_500L else 6_000L"),
]:
    if old_value not in s:
        raise SystemExit("GPS sampling anchor not found: " + old_value)
    s = s.replace(old_value, new_value, 1)
service.write_text(s, encoding="utf-8")

# 3) Update unit tests to make the new quality boundary explicit.
tests = root / "app/src/test/java/com/earthunlock/app/TrackMathTest.kt"
if not tests.exists():
    # The source package in the original archive is renamed by v0.8.1.
    candidates = list((root / "app/src/test/java").rglob("TrackMathTest.kt"))
    if len(candidates) != 1:
        raise SystemExit("TrackMathTest.kt not found uniquely")
    tests = candidates[0]
t = tests.read_text(encoding="utf-8")
t = t.replace("20.1f, 1_700_000_000_000L", "12.1f, 1_700_000_000_000L")
if "12f, 1_700_000_000_000L" not in t:
    anchor = "assertTrue(TrackMath.isValidFix(36.5, 127.8, 8f, 1_700_000_000_000L))"
    if anchor not in t:
        raise SystemExit("GPS accuracy unit-test anchor not found")
    t = t.replace(anchor, anchor + "\n        assertTrue(TrackMath.isValidFix(36.5, 127.8, 12f, 1_700_000_000_000L))", 1)
tests.write_text(t, encoding="utf-8")

# 4) Advance version; preserve package name and signing key.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 44' not in g or 'versionName = "0.9.0"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 44', 'versionCode = 45', 1)
g = g.replace('versionName = "0.9.0"', 'versionName = "0.9.1"', 1)
gradle.write_text(g, encoding="utf-8")
print("EARTH UNLOCK v0.9.1 fog overscan and GPS accuracy/sampling patch applied")
