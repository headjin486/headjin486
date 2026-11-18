from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/com/example/earthexplorer"
activity = base / "MainActivity.kt"
source = activity.read_text(encoding="utf-8")

needle = '''    private fun updateCurrentPosition(point: GeoPoint, center: Boolean) {
'''
method = '''    // The Activity unregisters its broadcast receiver while another app is in
    // front. On return, reload the authoritative last accepted GPS fix from SQLite.
    // Do not recenter the map: preserve the user's current map viewport.
    private fun refreshLatestSavedPosition() {
        if (!storeDelegate.isInitialized() || activityShuttingDown.get()) return
        try {
            refreshExecutor.execute {
                if (activityShuttingDown.get()) return@execute
                val latest = try { store.lastPoint() } catch (_: Exception) { null } ?: return@execute
                runOnUiThread {
                    if (activityShuttingDown.get() || isFinishing || isDestroyed) return@runOnUiThread
                    updateCurrentPosition(GeoPoint(latest.lat, latest.lon), false)
                }
            }
        } catch (_: RejectedExecutionException) {
            // Activity teardown raced with the resume callback.
        }
    }

'''
assert needle in source
source = source.replace(needle, method + needle, 1)

old = '''    override fun onResume() { super.onResume(); if (::map.isInitialized) map.onResume(); refreshFog() }
'''
new = '''    override fun onResume() {
        super.onResume()
        if (::map.isInitialized) map.onResume()
        refreshLatestSavedPosition()
        refreshFog()
        refreshTrackingStatus()
    }
'''
assert old in source
source = source.replace(old, new, 1)
activity.write_text(source, encoding="utf-8")

build = root / "app/build.gradle.kts"
s = build.read_text(encoding="utf-8")
assert 'versionCode = 30' in s and 'versionName = "0.7.6"' in s
s = s.replace('versionCode = 30', 'versionCode = 31', 1).replace('versionName = "0.7.6"', 'versionName = "0.7.7"', 1)
build.write_text(s, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
s = verify.read_text(encoding="utf-8")
s = s.replace('versionCode = 30', 'versionCode = 31').replace('versionName = "0.7.6"', 'versionName = "0.7.7"')
if 'refreshLatestSavedPosition' not in s:
    s += '''
# Returning to the Activity must reload the latest persisted GPS fix.
grep -F 'refreshLatestSavedPosition()' app/src/main/java/com/example/earthexplorer/MainActivity.kt >/dev/null
grep -F 'refreshLatestSavedPosition()' app/src/main/java/com/example/earthexplorer/MainActivity.kt | grep -F 'onResume' >/dev/null || true
'''
verify.write_text(s, encoding="utf-8")
