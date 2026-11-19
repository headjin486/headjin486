from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Track whether the user has manually taken control of the map viewport.
needle = "    private var centeredOnLiveFix = false\n"
if needle not in s:
    raise SystemExit("Live-fix state anchor not found")
s = s.replace(needle, needle + """    // Follow GPS automatically until the user manually pans or zooms the map.
    private var followUserLocation = true
    private var touchStartX = 0f
    private var touchStartY = 0f
    private var mapGestureMoved = false
    private val mapTouchSlop by lazy { android.view.ViewConfiguration.get(this).scaledTouchSlop }
""", 1)

# Apply a custom icon after marker creation (independent of localized title text).
needle = '        map.overlays.add(fog); map.overlays.add(currentMarker)\\n'
replacement = needle + '        currentMarker.icon = createCurrentLocationIcon()\\n        currentMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)\\n'
if needle not in s: raise SystemExit("Marker overlay insertion point not found")
s = s.replace(needle, replacement, 1)

# Keep the global percentage readable while retaining exact area below it.
old_percent = 'String.format(Locale.US, "%.10f%%", explorationPercent)'
new_percent = 'String.format(Locale.US, "%.8f%%", explorationPercent)'
if old_percent not in s: raise SystemExit("Exploration percentage formatter not found")
s = s.replace(old_percent, new_percent, 1)

# Detect actual user gestures without consuming touch events, so osmdroid keeps handling the map.
needle = '        mapFrame.addView(map)\n'
replacement = '''        mapFrame.addView(map)
        map.setOnTouchListener { _, event ->
            when (event.actionMasked) {
                android.view.MotionEvent.ACTION_DOWN -> {
                    touchStartX = event.x
                    touchStartY = event.y
                    mapGestureMoved = false
                }
                android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                    mapGestureMoved = true
                    followUserLocation = false
                }
                android.view.MotionEvent.ACTION_MOVE -> {
                    if (!mapGestureMoved) {
                        val dx = kotlin.math.abs(event.x - touchStartX)
                        val dy = kotlin.math.abs(event.y - touchStartY)
                        if (dx > mapTouchSlop || dy > mapTouchSlop) {
                            mapGestureMoved = true
                            followUserLocation = false
                        }
                    }
                }
            }
            false
        }
'''
if needle not in s: raise SystemExit("Map frame insertion point not found")
s = s.replace(needle, replacement, 1)

# Re-enable follow mode when the user taps the locate control.
needle = '    private fun goToCurrentLocation() {\n        val point = lastKnownPosition\n'
replacement = '''    private fun goToCurrentLocation() {
        followUserLocation = true
        val point = lastKnownPosition
'''
if needle not in s: raise SystemExit("Locate method anchor not found")
s = s.replace(needle, replacement, 1)

# Make every accepted GPS fix keep the viewport centered while follow mode is active.
needle = '        if (center) map.controller.animateTo(point)\n'
replacement = '        if (center || followUserLocation) map.controller.animateTo(point)\n'
if needle not in s: raise SystemExit("Position camera update not found")
s = s.replace(needle, replacement, 1)

# A simple vector-like marker: soft blue halo, white keyline, blue core.
needle = '    private fun goToCurrentLocation() {\n'
helper = '''    private fun createCurrentLocationIcon(): android.graphics.drawable.Drawable {
        val density = resources.displayMetrics.density
        val size = (32f * density).toInt().coerceAtLeast(32)
        val bitmap = android.graphics.Bitmap.createBitmap(
            size, size, android.graphics.Bitmap.Config.ARGB_8888
        )
        val canvas = android.graphics.Canvas(bitmap)
        val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)
        val center = size / 2f
        paint.color = Color.argb(48, 40, 132, 255)
        canvas.drawCircle(center, center, size * 0.48f, paint)
        paint.color = Color.WHITE
        canvas.drawCircle(center, center, size * 0.31f, paint)
        paint.color = Color.rgb(35, 126, 245)
        canvas.drawCircle(center, center, size * 0.235f, paint)
        paint.color = Color.WHITE
        canvas.drawCircle(center, center, size * 0.075f, paint)
        return android.graphics.drawable.BitmapDrawable(resources, bitmap)
    }

'''
if needle not in s: raise SystemExit("Location helper insertion point not found")
s = s.replace(needle, helper + needle, 1)

activity.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 38' not in g or 'versionName = "0.8.4"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 38', 'versionCode = 39', 1)
g = g.replace('versionName = "0.8.4"', 'versionName = "0.8.5"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 38', 'versionCode = 39')
v = v.replace('versionName = "0.8.4"', 'versionName = "0.8.5"')
v += """
# User-follow camera and custom current-position marker.
grep -F 'private var followUserLocation = true' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'if (center || followUserLocation) map.controller.animateTo(point)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'private fun createCurrentLocationIcon()' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'followUserLocation = false' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.5 custom location marker and follow-camera patch applied")
