from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/com/example/earthexplorer"
service = base / "LocationTrackingService.kt"
s = service.read_text(encoding="utf-8")

policy = r'''package com.example.earthexplorer

/** Conservative GPS duty-cycle policy: preserve high accuracy, reduce polling only while still. */
internal object TrackingPowerPolicy {
    const val MOVING_SPEED_METERS_PER_SECOND = 0.5f
    const val MOVING_DISPLACEMENT_METERS = 5f
    const val STILL_SAMPLES_BEFORE_SLOW_MODE = 3

    fun isMoving(speedMetersPerSecond: Float, displacementMeters: Float): Boolean =
        speedMetersPerSecond >= MOVING_SPEED_METERS_PER_SECOND ||
            displacementMeters >= MOVING_DISPLACEMENT_METERS
}
'''
(base / "TrackingPowerPolicy.kt").write_text(policy, encoding="utf-8")

assert "private val stopping = AtomicBoolean(false)" in s
s = s.replace(
'''    private val stopping = AtomicBoolean(false)
''',
'''    private val stopping = AtomicBoolean(false)
    // Keep 5-second high-accuracy fixes while moving. After three still samples,
    // reduce requests to 15 seconds; the first detected movement restores fast mode.
    private var fastTracking = false
    private var stationarySamples = 0
    private var lastMotionSample: android.location.Location? = null
    private var requestGeneration = 0
''', 1)

old = '''        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 5000L)
            .setMinUpdateIntervalMillis(3000L)
            .setMinUpdateDistanceMeters(3f)
            .build()

        callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                if (stopping.get()) return
                result.locations.forEach { loc ->
                    if (stopping.get()) return@forEach
                    // Ignore weak fixes; a 10 m reveal is not credible when GPS error is large.
'''
new = '''        callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                if (stopping.get()) return
                result.locations.forEach { loc ->
                    if (stopping.get()) return@forEach
                    // Ignore weak fixes; a 10 m reveal is not credible when GPS error is large.
'''
assert old in s
s = s.replace(old, new, 1)

# Only validated fixes are used for motion-state transitions.
valid_fix = '''                            loc.latitude, loc.longitude, loc.accuracy, loc.time
                        )) return@forEach
                    // Keep ordering deterministic'''
valid_fix_replacement = '''                            loc.latitude, loc.longitude, loc.accuracy, loc.time
                        )) return@forEach
                    updateAdaptiveTrackingMode(loc)
                    // Keep ordering deterministic'''
assert valid_fix in s
s = s.replace(valid_fix, valid_fix_replacement, 1)

needle = '''        try {
            fused.requestLocationUpdates(request, callback, mainLooper)
                .addOnFailureListener {
                    // Permission revocation and provider failures are reported
                    // asynchronously by Play services, not always as a thrown exception.
                    stopping.set(true)
                    stopSelf()
                }
        } catch (_: SecurityException) {
            stopping.set(true)
            stopSelf()
        }
    }

    private fun createChannel() {
'''
replacement = '''        requestLocationMode(fast = true)
    }

    private fun updateAdaptiveTrackingMode(location: android.location.Location) {
        val previous = lastMotionSample
        val displacement = previous?.distanceTo(location) ?: 0f
        val elapsedSeconds = previous?.let {
            ((location.time - it.time).coerceAtLeast(1L) / 1000f)
        } ?: 1f
        val speed = if (location.hasSpeed()) location.speed
            else displacement / elapsedSeconds
        val moving = TrackingPowerPolicy.isMoving(speed, displacement)

        if (moving) {
            stationarySamples = 0
            if (!fastTracking) requestLocationMode(fast = true)
        } else {
            stationarySamples += 1
            if (fastTracking &&
                stationarySamples >= TrackingPowerPolicy.STILL_SAMPLES_BEFORE_SLOW_MODE
            ) {
                requestLocationMode(fast = false)
            }
        }
        lastMotionSample = android.location.Location(location)
    }

    private fun requestLocationMode(fast: Boolean) {
        if (stopping.get() || !::fused.isInitialized || !::callback.isInitialized) return
        if (fastTracking == fast) return
        fastTracking = fast
        val generation = ++requestGeneration
        val interval = if (fast) 5_000L else 15_000L
        val minInterval = if (fast) 3_000L else 12_000L
        // Fast mode must receive periodic still samples; slow mode filters GPS drift.
        val minDistance = if (fast) 0f else 5f
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, interval)
            .setMinUpdateIntervalMillis(minInterval)
            .setMinUpdateDistanceMeters(minDistance)
            .build()
        try {
            fused.removeLocationUpdates(callback).addOnCompleteListener {
                // Ignore stale mode changes if another movement transition happened
                // while Play services was removing the previous request.
                if (stopping.get() || generation != requestGeneration) return@addOnCompleteListener
                try {
                    fused.requestLocationUpdates(request, callback, mainLooper)
                        .addOnFailureListener {
                            // Never silently continue if the provider rejects a mode change.
                            stopping.set(true)
                            stopSelf()
                        }
                } catch (_: SecurityException) {
                    stopping.set(true)
                    stopSelf()
                }
            }
        } catch (_: SecurityException) {
            stopping.set(true)
            stopSelf()
        }
    }

    private fun createChannel() {
'''
assert needle in s
s = s.replace(needle, replacement, 1)
service.write_text(s, encoding="utf-8")

# The visible Activity only needs to redraw fog periodically; the GPS service
# still persists every accepted fix and updates the live marker on each fix.
activity = base / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
assert "private val refreshGeneration = AtomicInteger(0)" in a
a = a.replace(
    "    private val refreshGeneration = AtomicInteger(0)\n",
    "    private val refreshGeneration = AtomicInteger(0)\n    private var lastLiveFogRefreshAt = 0L\n",
    1
)
old_receiver = """        override fun onReceive(context: Context?, intent: Intent?) {
            refreshFog()
            val lat = intent?.getDoubleExtra(LocationTrackingService.EXTRA_LAT, Double.NaN) ?: Double.NaN
"""
new_receiver = """        override fun onReceive(context: Context?, intent: Intent?) {
            val now = android.os.SystemClock.elapsedRealtime()
            if (now - lastLiveFogRefreshAt >= 10_000L) {
                lastLiveFogRefreshAt = now
                refreshFog()
            }
            val lat = intent?.getDoubleExtra(LocationTrackingService.EXTRA_LAT, Double.NaN) ?: Double.NaN
"""
assert old_receiver in a
a = a.replace(old_receiver, new_receiver, 1)
activity.write_text(a, encoding="utf-8")

test_dir = root / "app/src/test/java/com/example/earthexplorer"
test_dir.mkdir(parents=True, exist_ok=True)
(test_dir / "TrackingPowerPolicyTest.kt").write_text('''package com.example.earthexplorer

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TrackingPowerPolicyTest {
    @Test fun detectsWalkingAndVehicleMovement() {
        assertTrue(TrackingPowerPolicy.isMoving(1.2f, 2f))
        assertTrue(TrackingPowerPolicy.isMoving(0.1f, 8f))
    }

    @Test fun treatsSmallStationaryDriftAsStill() {
        assertFalse(TrackingPowerPolicy.isMoving(0.2f, 2f))
        assertFalse(TrackingPowerPolicy.isMoving(0f, 4.9f))
        assertTrue(TrackingPowerPolicy.isMoving(0f, 5f))
        assertTrue(TrackingPowerPolicy.isMoving(0.6f, 0.2f))
    }
}
''', encoding="utf-8")

build = root / "app/build.gradle.kts"
g = build.read_text(encoding="utf-8")
assert 'versionCode = 33' in g and 'versionName = "0.7.9"' in g
g = g.replace('versionCode = 33', 'versionCode = 34', 1)
g = g.replace('versionName = "0.7.9"', 'versionName = "0.8.0"', 1)
build.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 33', 'versionCode = 34')
v = v.replace('versionName = "0.7.9"', 'versionName = "0.8.0"')
v += '''
# Adaptive GPS policy must keep high accuracy and use slower polling only while still.
grep -F 'Priority.PRIORITY_HIGH_ACCURACY' "$SERVICE" >/dev/null
grep -F 'val interval = if (fast) 5_000L else 15_000L' "$SERVICE" >/dev/null
grep -F 'updateAdaptiveTrackingMode(loc)' "$SERVICE" >/dev/null
grep -F 'TrackingPowerPolicy.STILL_SAMPLES_BEFORE_SLOW_MODE' "$SERVICE" >/dev/null
grep -F 'TrackingPowerPolicy.isMoving' "$SERVICE" >/dev/null
grep -F 'lastLiveFogRefreshAt >= 10_000L' app/src/main/java/com/example/earthexplorer/MainActivity.kt >/dev/null
'''
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.0 adaptive GPS battery policy patch applied")
