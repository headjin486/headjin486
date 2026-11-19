from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Enable two-finger map rotation while keeping the GPS-follow state independent.
import_anchor = "import org.osmdroid.views.overlay.Marker\n"
if import_anchor not in s:
    raise SystemExit("osmdroid Marker import not found")
s = s.replace(import_anchor, import_anchor + "import org.osmdroid.views.overlay.gestures.RotationGestureOverlay\n", 1)

overlay_anchor = "        map.overlays.add(fog); map.overlays.add(currentMarker)\n"
if overlay_anchor not in s:
    raise SystemExit("Map overlay initialization anchor not found")
s = s.replace(
    overlay_anchor,
    overlay_anchor + """        map.setMapOrientation(0f)
        val rotationOverlay = RotationGestureOverlay(map).apply { isEnabled = true }
        map.overlays.add(rotationOverlay)
""",
    1
)

# Add a compact north-reset control beneath the existing location button.
locate_anchor = '        mapFrame.addView(locate, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply { topMargin = 18; marginEnd = 16 })\n'
if locate_anchor not in s:
    raise SystemExit("Locate button layout anchor not found")
compass = '''        val compassReset = Button(this).apply {
            text = "N ↑"
            textSize = 12f
            isAllCaps = false
            setTextColor(Color.rgb(10, 31, 58))
            contentDescription = "지도 방향을 북쪽으로 초기화"
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(Color.WHITE)
                cornerRadius = 24f
                setStroke(1, Color.LTGRAY)
            }
            elevation = 7f
            setOnClickListener {
                map.setMapOrientation(0f)
                map.invalidate()
            }
        }
        mapFrame.addView(compassReset, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply {
            topMargin = 82
            marginEnd = 16
        })
'''
s = s.replace(locate_anchor, locate_anchor + compass, 1)

# Multi-touch gestures (including rotation) must not disable GPS-follow mode.
old = '''                android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                    mapGestureMoved = true
                    followUserLocation = false
                }'''
new = '''                android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                    // Two-finger rotation/zoom is a map-orientation gesture, not a request
                    // to stop following the user's GPS position.
                    mapGestureMoved = true
                }'''
if old not in s:
    raise SystemExit("v0.8.5 multi-touch follow handler not found")
s = s.replace(old, new, 1)

activity.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 39' not in g or 'versionName = "0.8.5"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 39', 'versionCode = 40', 1)
g = g.replace('versionName = "0.8.5"', 'versionName = "0.8.6"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 39', 'versionCode = 40')
v = v.replace('versionName = "0.8.5"', 'versionName = "0.8.6"')
v += """
# Two-finger rotation and north-reset control.
grep -F 'RotationGestureOverlay(map)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'map.setMapOrientation(0f)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F '지도 방향을 북쪽으로 초기화' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.6 two-finger map rotation and north-reset patch applied")
