from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
fog = pkg / "FogOverlay.kt"
s = fog.read_text(encoding="utf-8")

old = """        val radiusMeters = cell * item.scale * 0.73
            val northLat = (lat + Math.toDegrees(radiusMeters / TrackMath.EARTH_RADIUS_METERS)).coerceAtMost(90.0)
            projection.toPixels(GeoPoint(northLat, lon), edge)
            val radiusPx = kotlin.math.abs(center.y - edge.y).toFloat().coerceAtLeast(1f)
            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, clearPaint)
"""
new = """        val radiusMeters = cell * item.scale * 0.73
            val northLat = (lat + Math.toDegrees(radiusMeters / TrackMath.EARTH_RADIUS_METERS)).coerceAtMost(90.0)
            projection.toPixels(GeoPoint(northLat, lon), edge)
            val radiusPx = kotlin.math.abs(center.y - edge.y).toFloat().coerceAtLeast(1f)
            // osmdroid rotates the map tiles, but this custom bitmap mask is screen-space.
            // Rotate only the reveal holes around the viewport center so the fog remains
            // edge-to-edge while revealed cells stay aligned with the rotated map.
            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, clearPaint)
"""
# Use a transform around the cell-render loop; it is intentionally isolated from fog fill.
anchor = """        val projection = mapView.projection
        val cell = TrackStore.CELL_METERS
"""
replace = """        val projection = mapView.projection
        val rotation = mapView.mapOrientation
        if (kotlin.math.abs(rotation) > 0.01f) {
            maskCanvas.save()
            maskCanvas.rotate(-rotation, bitmap.width / 2f, bitmap.height / 2f)
        }
        val cell = TrackStore.CELL_METERS
"""
if anchor not in s: raise SystemExit("Fog projection anchor missing")
s=s.replace(anchor,replace,1)
anchor2 = """            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, clearPaint)
        }
    }
}
"""
replace2 = """            maskCanvas.drawCircle(center.x.toFloat(), center.y.toFloat(), radiusPx, clearPaint)
        }
        if (kotlin.math.abs(rotation) > 0.01f) maskCanvas.restore()
    }
}
"""
if anchor2 not in s: raise SystemExit("Fog loop end anchor missing")
s=s.replace(anchor2,replace2,1)
fog.write_text(s,encoding="utf-8")

activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
old = """        mapFrame.addView(compassReset, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.END).apply {
            topMargin = 76
            marginEnd = 16
        })
"""
new = """        mapFrame.addView(compassReset, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.START).apply {
            topMargin = 18
            marginStart = 16
        })
"""
if old not in a: raise SystemExit("Compass layout anchor missing")
a=a.replace(old,new,1)
activity.write_text(a,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
if 'versionCode = 40' not in g or 'versionName = "0.8.6"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g=g.replace('versionCode = 40','versionCode = 41',1).replace('versionName = "0.8.6"','versionName = "0.8.7"',1)
gradle.write_text(g,encoding="utf-8")

verify=root/"scripts/verify-service-lifecycle.sh"
v=verify.read_text(encoding="utf-8").replace('versionCode = 40','versionCode = 41').replace('versionName = "0.8.6"','versionName = "0.8.7"')
v += """
# Rotated fog reveal mask and non-overlapping compass placement.
grep -F 'maskCanvas.rotate(-rotation' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'Gravity.TOP or Gravity.START' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v,encoding="utf-8")
print("EARTH UNLOCK v0.8.7 fog rotation alignment and compass placement patch applied")
