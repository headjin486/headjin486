from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Replace the glyph button with a custom-drawn, accessible location reticle.
old = """        val locate = Button(this).apply {
            text = "⌖"
            contentDescription = getString(R.string.current_location_button)
            textSize = 25f
            isAllCaps = false
            setTextColor(Color.rgb(35, 126, 245))
            setOnClickListener { goToCurrentLocation() }
            minWidth = dp(46)
            minimumWidth = dp(46)
            minHeight = dp(46)
            minimumHeight = dp(46)
            setPadding(0, 0, 0, dp(2))
            background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(Color.WHITE)
                setStroke(dp(1), Color.rgb(226, 233, 241))
            }
            elevation = dp(5).toFloat()
            stateListAnimator = null
        }
        mapFrame.addView(locate, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply { topMargin = 18; marginEnd = 16 })
"""
new = """        val locate = LocationControlView(this).apply {
            setOnClickListener { goToCurrentLocation() }
        }
        mapFrame.addView(locate, FrameLayout.LayoutParams(dp(48), dp(48), Gravity.TOP or Gravity.END).apply {
            topMargin = dp(18)
            marginEnd = dp(16)
        })
"""
if old not in s:
    raise SystemExit("v0.8.8 location button block not found")

s = s.replace(old, new, 1)

# Place the compass directly below the location control on the same edge.
old_layout = """        mapFrame.addView(compassReset, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.START).apply {
            topMargin = 18
            marginStart = 16
        })
"""
new_layout = """        mapFrame.addView(compassReset, FrameLayout.LayoutParams(dp(42), dp(42), Gravity.TOP or Gravity.END).apply {
            topMargin = dp(74)
            marginEnd = dp(19)
        })
"""
if old_layout not in s:
    raise SystemExit("Compass position block from v0.8.7 not found")
s = s.replace(old_layout, new_layout, 1)

# Animate the north reset instead of snapping the map orientation.
old_click = """            setOnClickListener {
                map.setMapOrientation(0f)
                map.invalidate()
                visibility = android.view.View.GONE
            }
"""
new_click = """            setOnClickListener {
                animateMapNorth { visibility = android.view.View.GONE }
            }
"""
if old_click not in s:
    raise SystemExit("Compass reset click block not found")
s = s.replace(old_click, new_click, 1)

# Animate zoom together with the existing smooth center animation.
s = s.replace(
    'if (point != null) { map.controller.setZoom(18.0); map.controller.animateTo(point); return }',
    'if (point != null) { map.controller.animateTo(point); animateZoomTo(18.0); return }',
    1
)
s = s.replace(
    'updateCurrentPosition(GeoPoint(loc.latitude, loc.longitude), true); map.controller.setZoom(18.0)',
    'updateCurrentPosition(GeoPoint(loc.latitude, loc.longitude), true); animateZoomTo(18.0)',
    1
)

anchor = "    private fun goToCurrentLocation() {"
if anchor not in s:
    raise SystemExit("goToCurrentLocation method missing")
helpers = """    private var zoomAnimator: android.animation.ValueAnimator? = null
    private var orientationAnimator: android.animation.ValueAnimator? = null

    private fun animateZoomTo(targetZoom: Double) {
        zoomAnimator?.cancel()
        val startZoom = map.zoomLevelDouble.toFloat()
        zoomAnimator = android.animation.ValueAnimator.ofFloat(startZoom, targetZoom.toFloat()).apply {
            duration = 320L
            interpolator = android.view.animation.DecelerateInterpolator()
            addUpdateListener { animator ->
                map.controller.setZoom((animator.animatedValue as Float).toDouble())
            }
            start()
        }
    }

    private fun animateMapNorth(onFinished: (() -> Unit)? = null) {
        orientationAnimator?.cancel()
        val start = map.mapOrientation
        val delta = ((-start + 540f) % 360f) - 180f
        orientationAnimator = android.animation.ValueAnimator.ofFloat(start, start + delta).apply {
            duration = 300L
            interpolator = android.view.animation.DecelerateInterpolator()
            addUpdateListener { animator ->
                map.setMapOrientation(animator.animatedValue as Float)
                map.invalidate()
            }
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: android.animation.Animator) {
                    map.setMapOrientation(0f)
                    map.invalidate()
                    onFinished?.invoke()
                }
            })
            start()
        }
    }

"""
s = s.replace(anchor, helpers + anchor, 1)

# Stop UI animators when the Activity is destroyed.
destroy_anchor = "    override fun onDestroy() {"
if destroy_anchor not in s:
    raise SystemExit("MainActivity onDestroy missing")
s = s.replace(destroy_anchor, destroy_anchor + """
        zoomAnimator?.cancel()
        orientationAnimator?.cancel()
""", 1)

# Add a custom-drawn location control: white circular surface and blue precision reticle.
if "private class LocationControlView" in s:
    raise SystemExit("LocationControlView already exists")
s += """

private class LocationControlView(context: android.content.Context) : android.view.View(context) {
    private val density = resources.displayMetrics.density
    private fun dp(value: Float) = value * density
    private val iconPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(35, 126, 245)
        style = android.graphics.Paint.Style.STROKE
        strokeWidth = dp(2.2f)
        strokeCap = android.graphics.Paint.Cap.ROUND
    }
    private val dotPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(35, 126, 245)
        style = android.graphics.Paint.Style.FILL
    }

    init {
        isClickable = true
        isFocusable = true
        contentDescription = context.getString(R.string.current_location_button)
        elevation = dp(5f)
        stateListAnimator = null
        val white = android.graphics.drawable.GradientDrawable().apply {
            shape = android.graphics.drawable.GradientDrawable.OVAL
            setColor(android.graphics.Color.WHITE)
            setStroke(dp(1f).toInt().coerceAtLeast(1), android.graphics.Color.rgb(226, 233, 241))
        }
        val mask = android.graphics.drawable.GradientDrawable().apply {
            shape = android.graphics.drawable.GradientDrawable.OVAL
            setColor(android.graphics.Color.WHITE)
        }
        background = android.graphics.drawable.RippleDrawable(
            android.content.res.ColorStateList.valueOf(android.graphics.Color.argb(38, 35, 126, 245)),
            white,
            mask
        )
    }

    override fun onDraw(canvas: android.graphics.Canvas) {
        super.onDraw(canvas)
        val cx = width / 2f
        val cy = height / 2f
        val outer = dp(8.2f)
        val armStart = dp(12f)
        val armEnd = dp(18f)
        canvas.drawCircle(cx, cy, outer, iconPaint)
        canvas.drawLine(cx, cy - armStart, cx, cy - armEnd, iconPaint)
        canvas.drawLine(cx, cy + armStart, cx, cy + armEnd, iconPaint)
        canvas.drawLine(cx - armStart, cy, cx - armEnd, cy, iconPaint)
        canvas.drawLine(cx + armStart, cy, cx + armEnd, cy, iconPaint)
        canvas.drawCircle(cx, cy, dp(2.6f), dotPaint)
    }
}
"""

activity.write_text(s, encoding="utf-8")

# Replace the old rotating rectangular fog bitmap with a viewport-sized alpha cutout.
# The fog itself is composited as a full-clip color layer; transparent bitmap edges
# can therefore never expose a rotated rectangular bitmap boundary.
fog = pkg / "FogOverlay.kt"
f = fog.read_text(encoding="utf-8")
if "private val erasePaint" not in f:
    field_anchor = "    private val bitmapPaint = Paint(Paint.FILTER_BITMAP_FLAG)\n"
    if field_anchor not in f:
        raise SystemExit("Fog bitmap paint anchor missing")
    f = f.replace(field_anchor, field_anchor + """    private val erasePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        xfermode = android.graphics.PorterDuffXfermode(android.graphics.PorterDuff.Mode.DST_OUT)
    }
    private val fogColor = Color.argb(244, 5, 13, 29)
""", 1)

start = f.index("    override fun draw(")
end = f.rfind("\n}")
methods = """    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return
        val width = canvas.width
        val height = canvas.height
        if (width <= 0 || height <= 0) return

        val rotation = mapView.mapOrientation
        var mask = cachedMask
        if (mask == null || mask.isRecycled || mask.width != width || mask.height != height ||
            kotlin.math.abs(rotation - cachedRotation) > 0.15f
        ) {
            clearCache()
            mask = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            renderMask(mask, mapView, rotation)
            cachedMask = mask
            cachedRotation = rotation
        }

        // Composite fog into an isolated layer, then punch out only explored cells.
        // Unlike a rotated opaque viewport bitmap, this has no rectangular edge to expose.
        val layer = canvas.saveLayer(0f, 0f, width.toFloat(), height.toFloat(), null)
        canvas.drawColor(fogColor)
        canvas.drawBitmap(mask, 0f, 0f, erasePaint)
        canvas.restoreToCount(layer)
    }

    private var cachedRotation: Float = Float.NaN

    private fun renderMask(bitmap: Bitmap, mapView: MapView, rotation: Float) {
        val maskCanvas = Canvas(bitmap)
        maskCanvas.drawColor(Color.TRANSPARENT, android.graphics.PorterDuff.Mode.CLEAR)
        val projection = mapView.projection
        val cell = TrackStore.CELL_METERS
        val center = Point()
        val edge = Point()
        val revealPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.FILL
        }

        // osmdroid rotates the map canvas. Counter-rotate the explored-cell cutouts
        // so they remain aligned with geography while the fog layer stays edge-to-edge.
        if (kotlin.math.abs(rotation) > 0.01f) {
            maskCanvas.save()
            maskCanvas.rotate(-rotation, bitmap.width / 2f, bitmap.height / 2f)
        }
        for (item in cells) {
            val lat = TrackMath.gridLatitudeDegrees(item.y, cell)
            val lon = TrackMath.gridLongitudeDegrees(item.x, cell)
            projection.toPixels(GeoPoint(lat, lon), center)
            val radiusMeters = cell * item.scale * 0.73
            val northLat = (lat + Math.toDegrees(radiusMeters / TrackMath.EARTH_RADIUS_METERS)).coerceAtMost(90.0)
            projection.toPixels(GeoPoint(northLat, lon), edge)
            val radiusPx = kotlin.math.abs(center.y - edge.y).toFloat().coerceAtLeast(1f)
            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, revealPaint)
        }
        if (kotlin.math.abs(rotation) > 0.01f) maskCanvas.restore()
    }
"""
f = f[:start] + methods + f[end:]
f = f.replace("        cachedMask = null\n", "        cachedMask = null\n        cachedRotation = Float.NaN\n", 1)
fog.write_text(f, encoding="utf-8")

# Bump to the next install-over version while preserving package and signing identity.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 42' not in g or 'versionName = "0.8.8"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 42', 'versionCode = 43', 1).replace('versionName = "0.8.8"', 'versionName = "0.8.9"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 42', 'versionCode = 43').replace('versionName = "0.8.8"', 'versionName = "0.8.9"')
# Update earlier-version assertions for the controls intentionally redesigned here.
v = v.replace("grep -F 'minWidth = dp(46)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null",
              "grep -F 'LocationControlView(this)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null")
v = v.replace("grep -F 'contentDescription = getString(R.string.current_location_button)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null",
              "grep -F 'contentDescription = context.getString(R.string.current_location_button)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null")
v = v.replace("grep -F 'text = \"⌖\"' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null",
              "grep -F 'LocationControlView(this)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null")
v = v.replace("grep -F 'Gravity.TOP or Gravity.START' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null",
              "grep -F 'topMargin = dp(74)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null")
v += """
# v0.8.9 animated map controls and edge-safe fog compositing.
grep -F 'LocationControlView(this)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'animateMapNorth' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'animateZoomTo(18.0)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'Gravity.TOP or Gravity.END' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'PorterDuff.Mode.DST_OUT' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'canvas.saveLayer' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.9 animated map controls and edge-safe fog patch applied")
