from pathlib import Path
import sys
r=Path(sys.argv[1]); b=r/'app/src/main/java/com/example/earthexplorer'
p=b/'TrackMath.kt'; s=p.read_text(); n='    /** Reject malformed fixes before they can enter the persistent GPS history or fog grid. */\n'
add='''    fun interpolationSteps(a: TrackPoint, b: TrackPoint, spacingMeters: Double = 5.0): Int {
        require(spacingMeters > 0.0 && spacingMeters.isFinite())
        val d = validSegmentDistanceMeters(a, b)
        return if (d <= 0.0) 1 else ceil(d / spacingMeters).toInt().coerceIn(1, 400)
    }
    fun interpolate(a: TrackPoint, b: TrackPoint, f: Double): TrackPoint {
        require(f in 0.0..1.0)
        var dl = b.lon - a.lon
        if (dl > 180.0) dl -= 360.0
        if (dl < -180.0) dl += 360.0
        var lon = a.lon + dl * f
        if (lon > 180.0) lon -= 360.0
        if (lon < -180.0) lon += 360.0
        return TrackPoint(a.lat + (b.lat-a.lat)*f, lon, max(a.accuracy,b.accuracy), a.time + ((b.time-a.time)*f).toLong())
    }
'''
assert n in s; p.write_text(s.replace(n,add+n,1))
p=b/'TrackStore.kt'; s=p.read_text(); old='''            insertPointAndUpdateStats(db, point)
            insertRevealCells(db, point, radiusMeters)
            db.setTransactionSuccessful()
'''; new='''            val previous = readLastPoint(db)
            insertPointAndUpdateStats(db, point)
            if (previous != null) {
                val steps = TrackMath.interpolationSteps(previous, point, 5.0)
                if (steps > 1) for (step in 1 until steps)
                    insertRevealCells(db, TrackMath.interpolate(previous, point, step.toDouble() / steps), radiusMeters)
            }
            insertRevealCells(db, point, radiusMeters)
            db.setTransactionSuccessful()
'''; assert old in s; p.write_text(s.replace(old,new,1))
p=b/'FogOverlay.kt'; s=p.read_text().replace('import android.graphics.Path\n','')
s=s.replace('''        val p1 = Point(); val p2 = Point(); val p3 = Point(); val p4 = Point()
        val path = Path()
''','''        val center = Point(); val edge = Point()
''')
start=s.index('''            val south = TrackMath.gridLatitudeDegrees(item.y - item.scale / 2.0, cell)''')
end=s.index('''        }
    }
}''',start)
s=s[:start]+'''            val lat = TrackMath.gridLatitudeDegrees(item.y, cell)
            val lon = TrackMath.gridLongitudeDegrees(item.x, cell)
            projection.toPixels(GeoPoint(lat, lon), center)
            val radiusMeters = cell * item.scale * 0.73
            val northLat = (lat + Math.toDegrees(radiusMeters / TrackMath.EARTH_RADIUS_METERS)).coerceAtMost(90.0)
            projection.toPixels(GeoPoint(northLat, lon), edge)
            val radiusPx = kotlin.math.abs(center.y - edge.y).toFloat().coerceAtLeast(1f)
            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, clearPaint)
'''+s[end:]; p.write_text(s)
p=b/'MainActivity.kt'; s=p.read_text().replace('import android.widget.LinearLayout\n','import android.widget.LinearLayout\nimport android.widget.FrameLayout\n')
s=s.replace('    private var centeredOnLiveFix = false\n','    private var centeredOnLiveFix = false\n    private var lastKnownPosition: GeoPoint? = null\n')
s=s.replace('''        root.addView(map)
''','''        val mapFrame = FrameLayout(this)
        map.layoutParams = FrameLayout.LayoutParams(-1, -1)
        mapFrame.addView(map)
        val locate = Button(this).apply {
            text = "◎ 내 위치"; textSize = 13f; isAllCaps = false
            setTextColor(Color.rgb(10, 31, 58)); setOnClickListener { goToCurrentLocation() }
            background = android.graphics.drawable.GradientDrawable().apply { setColor(Color.WHITE); cornerRadius = 28f; setStroke(1, Color.LTGRAY) }
            elevation = 8f
        }
        mapFrame.addView(locate, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply { topMargin = 18; marginEnd = 16 })
        root.addView(mapFrame, LinearLayout.LayoutParams(-1, 0, 1f))
''',1)
s=s.replace('textSize = 16f; setTextColor(Color.WHITE); setPadding(2, 2, 2, 10)','textSize = 18f; setTextColor(Color.WHITE); setPadding(2, 4, 2, 12); setLineSpacing(3f, 1.05f)')
s=s.replace('String.format(Locale.US, "%.3g%%", explorationPercent)','String.format(Locale.US, "%.10f%%", explorationPercent)')
s=s.replace('''        currentMarker.position = point
''','''        lastKnownPosition = point
        currentMarker.position = point
''')
needle='    override fun onStart() {\n'
method='''    private fun goToCurrentLocation() {
        val point = lastKnownPosition
        if (point != null) { map.controller.setZoom(18.0); map.controller.animateTo(point); return }
        com.google.android.gms.location.LocationServices.getFusedLocationProviderClient(this).lastLocation.addOnSuccessListener { loc ->
            if (loc != null && !isFinishing && !isDestroyed) {
                updateCurrentPosition(GeoPoint(loc.latitude, loc.longitude), true); map.controller.setZoom(18.0)
            } else android.widget.Toast.makeText(this, "현재 위치를 확인하지 못했습니다. 자동 탐험을 시작해 주세요.", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

'''
assert needle in s; s=s.replace(needle,method+needle,1)
s=s.replace('EarthExplorer/0.7.4','EarthExplorer/0.7.6'); p.write_text(s)
p=r/'app/build.gradle.kts'; s=p.read_text().replace('versionCode = 29','versionCode = 30').replace('versionName = "0.7.5"','versionName = "0.7.6"'); p.write_text(s)
p=r/'scripts/verify-service-lifecycle.sh'; s=p.read_text().replace('versionCode = 29','versionCode = 30').replace('versionName = "0.7.5"','versionName = "0.7.6"'); p.write_text(s)
