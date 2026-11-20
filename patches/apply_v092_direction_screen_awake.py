from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"

# 1) The requested exploration reveal radius is 12 metres (not the GPS
# horizontal-accuracy acceptance threshold, which remains 12 metres too).
service = pkg / "LocationTrackingService.kt"
s = service.read_text(encoding="utf-8")
if "store.recordAndReveal(point, 10.0)" not in s:
    raise SystemExit("Expected v0.9.1 10m reveal call not found")
s = s.replace("store.recordAndReveal(point, 10.0)", "store.recordAndReveal(point, 12.0)", 1)
service.write_text(s, encoding="utf-8")

store = pkg / "TrackStore.kt"
t = store.read_text(encoding="utf-8")
if "fun recordAndReveal(point: TrackPoint, radiusMeters: Double = 10.0)" not in t:
    raise SystemExit("TrackStore default 10m reveal radius anchor not found")
t = t.replace(
    "fun recordAndReveal(point: TrackPoint, radiusMeters: Double = 10.0)",
    "fun recordAndReveal(point: TrackPoint, radiusMeters: Double = 12.0)",
    1
)
store.write_text(t, encoding="utf-8")

# 2) Keep the display awake while this Activity is in the foreground.
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
if "FLAG_KEEP_SCREEN_ON" in a:
    raise SystemExit("Keep-screen-on flag already exists")
on_create = "    override fun onCreate(savedInstanceState: Bundle?) {\n        super.onCreate(savedInstanceState)\n"
if on_create not in a:
    raise SystemExit("MainActivity onCreate anchor not found")
a = a.replace(
    on_create,
    on_create + """        // Prevent automatic screen timeout while the app is visible.
        // The flag is scoped to this Activity window and does not keep the display
        // awake after the user switches to another app.
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
""",
    1
)

# 3) Send a movement heading with each accepted GPS fix. Prefer the fused GPS
# bearing while moving; otherwise derive direction from consecutive accepted fixes.
companion_anchor = "        const val EXTRA_LON = \"longitude\"\n"
if companion_anchor not in s:
    raise SystemExit("Location service EXTRA_LON constant not found")
s = s.replace(
    companion_anchor,
    companion_anchor + "        const val EXTRA_BEARING = \"bearing_degrees\"\n",
    1
)
broadcast_anchor = """                                sendBroadcast(Intent(ACTION_TRACK_UPDATED).setPackage(packageName).apply {
                                    putExtra(EXTRA_LAT, loc.latitude)
                                    putExtra(EXTRA_LON, loc.longitude)
                                })
"""
broadcast_replacement = """                                val movementBearing = when {
                                    loc.hasBearing() && loc.hasSpeed() && loc.speed >= 0.8f ->
                                        loc.bearing
                                    previous != null && previous.distanceTo(loc) >= 3f ->
                                        previous.bearingTo(loc)
                                    else -> Float.NaN
                                }
                                sendBroadcast(Intent(ACTION_TRACK_UPDATED).setPackage(packageName).apply {
                                    putExtra(EXTRA_LAT, loc.latitude)
                                    putExtra(EXTRA_LON, loc.longitude)
                                    putExtra(EXTRA_BEARING, movementBearing)
                                })
"""
if broadcast_anchor not in s:
    raise SystemExit("Accepted GPS broadcast block not found")
s = s.replace(broadcast_anchor, broadcast_replacement, 1)
service.write_text(s, encoding="utf-8")

# 4) Retain the most recent valid course and align the map to that course
# only when the user taps the location button. The map heading is animated.
receiver_anchor = """            val lon = intent?.getDoubleExtra(LocationTrackingService.EXTRA_LON, Double.NaN) ?: Double.NaN
            if (!lat.isNaN() && !lon.isNaN())"""
receiver_replacement = """            val lon = intent?.getDoubleExtra(LocationTrackingService.EXTRA_LON, Double.NaN) ?: Double.NaN
            val bearing = intent?.getFloatExtra(LocationTrackingService.EXTRA_BEARING, Float.NaN) ?: Float.NaN
            if (bearing.isFinite()) lastKnownBearing = ((bearing % 360f) + 360f) % 360f
            if (!lat.isNaN() && !lon.isNaN())"""
if receiver_anchor not in a:
    raise SystemExit("Tracking receiver latitude/longitude anchor not found")
a = a.replace(receiver_anchor, receiver_replacement, 1)

state_anchor = "    private var lastKnownPosition: GeoPoint? = null\n"
if state_anchor not in a:
    raise SystemExit("Last-known position state anchor not found")
a = a.replace(state_anchor, state_anchor + "    private var lastKnownBearing: Float? = null\n", 1)

# Replace the existing north-only animation with a reusable shortest-path rotation.
start = a.find("    private fun animateMapNorth(")
if start < 0:
    raise SystemExit("Existing animateMapNorth method not found")
end = a.find("    private fun goToCurrentLocation()", start)
if end < 0:
    raise SystemExit("goToCurrentLocation boundary not found")
new_methods = """    private fun animateMapOrientation(targetOrientation: Float, onFinished: (() -> Unit)? = null) {
        orientationAnimator?.cancel()
        val start = map.mapOrientation
        val normalizedTarget = ((targetOrientation % 360f) + 360f) % 360f
        val delta = ((normalizedTarget - start + 540f) % 360f) - 180f
        orientationAnimator = android.animation.ValueAnimator.ofFloat(start, start + delta).apply {
            duration = 360L
            interpolator = android.view.animation.DecelerateInterpolator()
            addUpdateListener { animator ->
                map.setMapOrientation(animator.animatedValue as Float)
                map.invalidate()
            }
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: android.animation.Animator) {
                    map.setMapOrientation(normalizedTarget)
                    map.invalidate()
                    onFinished?.invoke()
                }
            })
            start()
        }
    }

    private fun animateMapNorth(onFinished: (() -> Unit)? = null) {
        animateMapOrientation(0f, onFinished)
    }

"""
a = a[:start] + new_methods + a[end:]

# Align travel direction to the top of the screen when the location control is tapped.
go_anchor = "    private fun goToCurrentLocation() {\n        followUserLocation = true\n"
if go_anchor not in a:
    raise SystemExit("Location button handler anchor not found")
a = a.replace(
    go_anchor,
    go_anchor + """        lastKnownBearing?.let { bearing ->
            // Map orientation is the inverse of travel bearing: the direction of
            // movement is placed at the top of the screen (12 o'clock).
            animateMapOrientation(-bearing)
        }
""",
    1
)

activity.write_text(a, encoding="utf-8")

# 5) Bump app version for a safe install-over update.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 45' not in g or 'versionName = "0.9.1"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 45', 'versionCode = 46', 1)
g = g.replace('versionName = "0.9.1"', 'versionName = "0.9.2"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 45', 'versionCode = 46')
v = v.replace('versionName = "0.9.1"', 'versionName = "0.9.2"')
v += """
# v0.9.2 reveal radius, foreground keep-screen-on, and travel-heading recenter.
grep -F 'store.recordAndReveal(point, 12.0)' app/src/main/java/com/earthunlock/app/LocationTrackingService.kt >/dev/null
grep -F 'radiusMeters: Double = 12.0' app/src/main/java/com/earthunlock/app/TrackStore.kt >/dev/null
grep -F 'FLAG_KEEP_SCREEN_ON' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'EXTRA_BEARING' app/src/main/java/com/earthunlock/app/LocationTrackingService.kt >/dev/null
grep -F 'animateMapOrientation(-bearing)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'private var lastKnownBearing: Float? = null' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.2 12m reveal, keep-screen-on, and travel-heading patch applied")
