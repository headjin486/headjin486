from pathlib import Path
import sys

root = Path(sys.argv[1])
main = root / "app/src/main/java/com/example/earthexplorer/MainActivity.kt"
service = root / "app/src/main/java/com/example/earthexplorer/LocationTrackingService.kt"
gradle = root / "app/build.gradle.kts"
verify = root / "scripts/verify-service-lifecycle.sh"

s = main.read_text()
repls = [
('    private lateinit var countText: TextView\n', '    private lateinit var countText: TextView\n    private lateinit var trackingStatusText: TextView\n'),
('            controller.setZoom(4.0); controller.setCenter(GeoPoint(36.5, 127.8))\n', '            controller.setZoom(17.0); controller.setCenter(GeoPoint(36.5, 127.8))\n'),
('''        countText = TextView(this).apply { textSize = 15f; setTextColor(Color.WHITE) }
        panel.addView(countText)
''', '''        countText = TextView(this).apply { textSize = 16f; setTextColor(Color.WHITE); setPadding(2, 2, 2, 10) }
        trackingStatusText = TextView(this).apply { textSize = 15f; setTextColor(Color.rgb(255, 210, 90)); setPadding(2, 0, 2, 10) }
        panel.addView(countText)
        panel.addView(trackingStatusText)
'''),
('''        val refresh = Button(this).apply { text = "지도 갱신"; setOnClickListener { refreshFog() } }
        val settings = Button(this).apply { text = "위치 권한 설정"; setOnClickListener { openAppSettings() } }
        row2.addView(refresh, LinearLayout.LayoutParams(0, -2, 1f)); row2.addView(settings, LinearLayout.LayoutParams(0, -2, 1f))
''', '''        val settings = Button(this).apply { text = "위치 권한 설정"; setOnClickListener { openAppSettings() } }
        row2.addView(settings, LinearLayout.LayoutParams(-1, -2, 1f))
'''),
('''        store.lastPoint()?.let { last ->
            val point = GeoPoint(last.lat, last.lon)
            updateCurrentPosition(point, true)
            centeredOnLiveFix = true
        }
        refreshFog()
''', '''        val lastSavedPoint = store.lastPoint()
        lastSavedPoint?.let { last ->
            val point = GeoPoint(last.lat, last.lon)
            map.controller.setZoom(17.0)
            updateCurrentPosition(point, true)
            centeredOnLiveFix = true
        }
        restoreMapViewportIfAvailable(keepCurrentCenter = lastSavedPoint != null)
        refreshTrackingStatus()
        refreshFog()
'''),
('''                    countText.text = "자동 탐험을 시작했습니다. 알림에서 추적 상태를 확인할 수 있습니다."
''', '''                    trackingStatusText.text = "● 탐험 시작 요청됨 · GPS 연결 확인 중"
                    refreshTrackingStatus()
'''),
('''                    val visibleGpsCount = store.visibleCount(north, east, south, west)
                    val aggregationFactor''', '''                    val aggregationFactor'''),
('''                    val distance = store.distanceMeters()
                    val area = store.exploredAreaSquareMeters()
                    val totalPoints = store.count()
                    val totalCells = store.exploredCellCount()
''', '''                    val area = store.exploredAreaSquareMeters()
'''),
('''                        val distanceLabel = if (distance >= 1000)
                            String.format(Locale.getDefault(), "%.2f km", distance / 1000)
                        else String.format(Locale.getDefault(), "%.0f m", distance)
                        val areaLabel = if (area >= 1_000_000.0)
                            String.format(Locale.getDefault(), "%.3f km²", area / 1_000_000.0)
                        else String.format(Locale.getDefault(), "%.0f m²", area)
                        countText.text = "저장된 GPS 기록 ${totalPoints}개 · 누적 이동 거리(추정) $distanceLabel\\n" +
                            "누적 공개 면적(격자 추정) $areaLabel · 공개 셀 ${totalCells}개\\n" +
                            "현재 화면 GPS ${visibleGpsCount}개 · 현재 화면 공개 격자 ${visibleCells.size}개\\n" +
                            "※ 지도 축척별 공개 격자 집계 표시 · 집계 배율 ${aggregationFactor}x · 육지 면적·세계 탐험률은 아직 미구현입니다."
''', '''                        val earthSurfaceAreaM2 = 4.0 * Math.PI * TrackMath.EARTH_RADIUS_METERS * TrackMath.EARTH_RADIUS_METERS
                        val explorationPercent = (area / earthSurfaceAreaM2) * 100.0
                        val areaLabel = if (area >= 1_000_000.0)
                            String.format(Locale.getDefault(), "%.3f km²", area / 1_000_000.0)
                        else String.format(Locale.getDefault(), "%,.0f m²", area)
                        val percentLabel = String.format(Locale.US, "%.3g%%", explorationPercent)
                        countText.text = "🌍 지구 탐험률\\n$percentLabel\\n공개 면적 $areaLabel"
                        refreshTrackingStatus()
'''),
('''    private fun updateCurrentPosition(point: GeoPoint, center: Boolean) {
''', '''    private fun refreshTrackingStatus() {
        if (!::trackingStatusText.isInitialized) return
        val running = LocationTrackingService.isRunning
        trackingStatusText.text = if (running) "● 자동 탐험 중 · GPS 위치 수신/기록 중" else "● 탐험 중지됨"
        trackingStatusText.setTextColor(if (running) Color.rgb(92, 220, 130) else Color.rgb(255, 190, 100))
    }

    private fun restoreMapViewportIfAvailable(keepCurrentCenter: Boolean) {
        val prefs = getSharedPreferences("map_viewport", MODE_PRIVATE)
        val savedZoom = prefs.getFloat("zoom", Float.NaN)
        if (!savedZoom.isNaN()) map.controller.setZoom(savedZoom.toDouble())
        if (!keepCurrentCenter) {
            val savedLat = prefs.getFloat("lat", Float.NaN)
            val savedLon = prefs.getFloat("lon", Float.NaN)
            if (!savedLat.isNaN() && !savedLon.isNaN()) map.controller.setCenter(GeoPoint(savedLat.toDouble(), savedLon.toDouble()))
        }
    }

    private fun saveMapViewport() {
        if (!::map.isInitialized) return
        val center = map.mapCenter as? GeoPoint ?: return
        getSharedPreferences("map_viewport", MODE_PRIVATE).edit()
            .putFloat("zoom", map.zoomLevelDouble.toFloat())
            .putFloat("lat", center.latitude.toFloat())
            .putFloat("lon", center.longitude.toFloat())
            .apply()
    }

    private fun updateCurrentPosition(point: GeoPoint, center: Boolean) {
'''),
('''        refreshFog()
    }
    override fun onStop()''', '''        refreshTrackingStatus()
        refreshFog()
    }
    override fun onStop()'''),
('''    override fun onPause() { if (::map.isInitialized) map.onPause(); super.onPause() }
''', '''    override fun onPause() { if (::map.isInitialized) { saveMapViewport(); map.onPause() }; super.onPause() }
''')
]
for old, new in repls:
    if old not in s:
        raise SystemExit("MainActivity patch anchor missing: " + old[:90].replace("\n", " "))
    s = s.replace(old, new, 1)
main.write_text(s)

s = service.read_text()
old = '        const val ACTION_STOP = "com.example.earthexplorer.STOP_TRACKING"\n'
new = old + '        @Volatile var isRunning: Boolean = false\n            private set\n'
assert old in s
s = s.replace(old, new, 1)
old = '''                startForeground(41, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            } else {
                startForeground(41, notification)
            }
'''
new = old + '            isRunning = true\n'
assert old in s
s = s.replace(old, new, 1)
s = s.replace('''            stopping.set(true)
            if (::fused.isInitialized && ::callback.isInitialized) fused.removeLocationUpdates(callback)
            stopForeground(STOP_FOREGROUND_REMOVE)
''', '''            stopping.set(true)
            isRunning = false
            if (::fused.isInitialized && ::callback.isInitialized) fused.removeLocationUpdates(callback)
            stopForeground(STOP_FOREGROUND_REMOVE)
''', 1)
s = s.replace('''    override fun onDestroy() {
        stopping.set(true)
''', '''    override fun onDestroy() {
        stopping.set(true)
        isRunning = false
''', 1)
service.write_text(s)

g = gradle.read_text().replace('versionCode = 28', 'versionCode = 29').replace('versionName = "0.7.4"', 'versionName = "0.7.5"')
gradle.write_text(g)

v = verify.read_text().replace('versionCode = 28', 'versionCode = 29').replace('versionName = "0.7.4"', 'versionName = "0.7.5"')
v = v.replace("printf 'Service lifecycle static checks: 7/7 passed.\\n'", "grep -F 'isRunning = true' \"$SERVICE\" >/dev/null\\ngrep -F 'isRunning = false' \"$SERVICE\" >/dev/null\\nprintf 'Service lifecycle static checks: 9/9 passed.\\n'")
verify.write_text(v)
print("EARTH UNLOCK v0.7.5 patch applied")
