from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Restore the original text-based "내위치" control.
old = """        val locate = LocationControlView(this).apply {
            setOnClickListener { goToCurrentLocation() }
        }
        mapFrame.addView(locate, FrameLayout.LayoutParams(dp(48), dp(48), Gravity.TOP or Gravity.END).apply {
            topMargin = dp(18)
            marginEnd = dp(16)
        })
"""
new = """        val locate = Button(this).apply {
            text = getString(R.string.current_location_button)
            setOnClickListener { goToCurrentLocation() }
            styleActionButton(this, primary = false, floating = true)
        }
        mapFrame.addView(locate, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply {
            topMargin = dp(18)
            marginEnd = dp(16)
        })
"""
if old not in s:
    raise SystemExit("v0.8.9 custom location control block not found")
s = s.replace(old, new, 1)

# Remove the custom-drawn reticle class entirely.
marker = "\n\nprivate class LocationControlView"
if marker not in s:
    raise SystemExit("LocationControlView class marker missing")
s = s[:s.index(marker)].rstrip() + "\n"
activity.write_text(s, encoding="utf-8")

# Draw fog and reveal holes directly in the same rotated canvas as map overlays.
# This removes the independently transformed bitmap mask, which caused geographic drift.
fog = pkg / "FogOverlay.kt"
f = fog.read_text(encoding="utf-8")
start = f.index("    override fun draw(")
end = f.rfind("\n}")
method = """    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return
        val width = mapView.width
        val height = mapView.height
        if (width <= 0 || height <= 0) return

        val layer = canvas.saveLayer(0f, 0f, width.toFloat(), height.toFloat(), null)
        canvas.drawColor(fogColor)

        // Use the very same overlay canvas/projection transform as the map itself.
        // No bitmap, cached screen coordinates, or compensating counter-rotation:
        // explored cells and map tiles therefore rotate as one coordinate system.
        val projection = mapView.projection
        val cell = TrackStore.CELL_METERS
        val center = Point()
        val edge = Point()
        for (item in cells) {
            val lat = TrackMath.gridLatitudeDegrees(item.y, cell)
            val lon = TrackMath.gridLongitudeDegrees(item.x, cell)
            projection.toPixels(GeoPoint(lat, lon), center)
            val radiusMeters = cell * item.scale * 0.73
            val northLat = (lat + Math.toDegrees(radiusMeters / TrackMath.EARTH_RADIUS_METERS)).coerceAtMost(90.0)
            projection.toPixels(GeoPoint(northLat, lon), edge)
            val radiusPx = kotlin.math.abs(center.y - edge.y).toFloat().coerceAtLeast(1f)
            canvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, erasePaint)
        }
        canvas.restoreToCount(layer)
    }
"""
f = f[:start] + method + f[end:]
fog.write_text(f, encoding="utf-8")

# Advance version without changing application ID or signing configuration.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 43' not in g or 'versionName = "0.8.9"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 43', 'versionCode = 44', 1)
g = g.replace('versionName = "0.8.9"', 'versionName = "0.9.0"', 1)
gradle.write_text(g, encoding="utf-8")

# Align the verifier with the restored text control and shared-canvas fog renderer.
verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 43', 'versionCode = 44')
v = v.replace('versionName = "0.8.9"', 'versionName = "0.9.0"')
v = "\n".join(line for line in v.splitlines()
               if "LocationControlView" not in line
               and "contentDescription = context.getString(R.string.current_location_button)" not in line)
v += """
# v0.9.0: text-based locate button and shared map/fog canvas transform.
grep -F 'text = getString(R.string.current_location_button)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'styleActionButton(this, primary = false, floating = true)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
! grep -F 'private class LocationControlView' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'canvas.saveLayer' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'canvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, erasePaint)' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
! grep -F 'maskCanvas.rotate(-rotation' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.0 shared-canvas fog and original text location button patch applied")
