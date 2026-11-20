from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

old = """            if (bearing.isFinite()) lastKnownBearing = ((bearing % 360f) + 360f) % 360f
"""
new = """            if (bearing.isFinite()) {
                val normalizedBearing = ((bearing % 360f) + 360f) % 360f
                lastKnownBearing = normalizedBearing

                // While follow mode is active, keep the direction of travel at
                // the top of the screen. Compare against the last applied heading
                // so small GPS course changes accumulate instead of being lost.
                val previousApplied = lastAppliedBearing
                val headingDelta = if (previousApplied == null) 180f else
                    kotlin.math.abs(((normalizedBearing - previousApplied + 540f) % 360f) - 180f)
                if (followUserLocation && (previousApplied == null || headingDelta >= 4f)) {
                    lastAppliedBearing = normalizedBearing
                    animateMapOrientation(-normalizedBearing)
                }
            }
"""
if old not in a:
    raise SystemExit("v0.9.2 bearing receiver anchor not found")
a = a.replace(old, new, 1)

state = "    private var lastKnownBearing: Float? = null\n"
if state not in a:
    raise SystemExit("lastKnownBearing state not found")
a = a.replace(state, state + "    private var lastAppliedBearing: Float? = null\n", 1)

tap = """        lastKnownBearing?.let { bearing ->
            // Map orientation is the inverse of travel bearing: the direction of
            // movement is placed at the top of the screen (12 o'clock).
            animateMapOrientation(-bearing)
        }
"""
tap_new = """        lastKnownBearing?.let { bearing ->
            // Map orientation is the inverse of travel bearing: the direction of
            // movement is placed at the top of the screen (12 o'clock).
            lastAppliedBearing = bearing
            animateMapOrientation(-bearing)
        }
"""
if tap not in a:
    raise SystemExit("location button bearing alignment block not found")
a = a.replace(tap, tap_new, 1)

activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 46' not in g or 'versionName = "0.9.2"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 46', 'versionCode = 47', 1)
g = g.replace('versionName = "0.9.2"', 'versionName = "0.9.3"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 46', 'versionCode = 47')
v = v.replace('versionName = "0.9.2"', 'versionName = "0.9.3"')
v += """
# v0.9.3 continuously aligns the follow camera to the latest movement bearing.
grep -F 'private var lastAppliedBearing: Float? = null' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'if (followUserLocation && (previousApplied == null || headingDelta >= 4f))' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'animateMapOrientation(-normalizedBearing)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.3 continuous travel-heading follow patch applied")
