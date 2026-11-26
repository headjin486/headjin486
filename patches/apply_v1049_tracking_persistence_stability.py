"""Keep GPS fixes independent of optional country lookup and reduce SQLite work."""
from pathlib import Path
import sys
root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")
src = root / "app/src/main/java/com/earthunlock/app"

def mutate(path, edit):
    old = path.read_text(encoding="utf-8")
    path.write_text(edit(old), encoding="utf-8")

def replace(s, old, new):
    assert s.count(old) == 1, f"Anchor mismatch: {old[:120]}"
    return s.replace(old, new, 1)

def store_edit(s):
    # Preserve the existing traversal, interpolation, and per-cell insertion logic.
    # One prepared statement and one stats update for the entire GPS transaction.
    s = replace(s, """            val previous = readLastPoint(db)
            insertPointAndUpdateStats(db, point)
            if (previous != null) {
                val steps = TrackMath.interpolationSteps(previous, point, 5.0)
                if (steps > 1) for (step in 1 until steps)
                    insertRevealCells(db, TrackMath.interpolate(previous, point, step.toDouble() / steps), radiusMeters)
            }
            insertRevealCells(db, point, radiusMeters)""", """            ensureDistanceStatsInitialized(db)
            val previous = readLastPoint(db)
            insertPointAndUpdateStats(db, point)
            ensureExploredAreaStatsInitialized(db)
            db.compileStatement("INSERT OR IGNORE INTO explored_cells(cell_x, cell_y) VALUES(?,?)").use { statement ->
                var addedArea = 0.0
                if (previous != null) {
                    val steps = TrackMath.interpolationSteps(previous, point, 5.0)
                    if (steps > 1) for (step in 1 until steps)
                        addedArea += insertRevealCells(statement, TrackMath.interpolate(previous, point, step.toDouble() / steps), radiusMeters)
                }
                addedArea += insertRevealCells(statement, point, radiusMeters)
                addRevealedArea(db, addedArea)
            }""")
    # Stream legacy stats instead of keeping all points on heap. Preserve timestamp/_id order.
    s = replace(s, """        val points = queryWithDatabase(db, "SELECT lat, lon, accuracy, time FROM points ORDER BY time, _id", null)
        var total = 0.0
        for (i in 1 until points.size) total += validSegmentDistance(points[i - 1], points[i])
        val last = points.lastOrNull()""", """        var total = 0.0
        var last: TrackPoint? = null
        db.rawQuery("SELECT lat, lon, accuracy, time FROM points ORDER BY time, _id", null).use { c ->
            while (c.moveToNext()) {
                val next = TrackPoint(c.getDouble(0), c.getDouble(1), c.getFloat(2), c.getLong(3))
                last?.let { total += validSegmentDistance(it, next) }
                last = next
            }
        }""")
    a=s.index("    private fun queryWithDatabase(")
    b=s.index("    private fun validSegmentDistance(", a)
    s=s[:a]+s[b:]
    s=replace(s, """            insertRevealCells(db, point, radiusMeters)
            db.setTransactionSuccessful()""", """            ensureExploredAreaStatsInitialized(db)
            db.compileStatement("INSERT OR IGNORE INTO explored_cells(cell_x, cell_y) VALUES(?,?)").use { statement ->
                addRevealedArea(db, insertRevealCells(statement, point, radiusMeters))
            }
            db.setTransactionSuccessful()""")
    s=replace(s, """    private fun insertRevealCells(db: SQLiteDatabase, point: TrackPoint, radiusMeters: Double) {
        ensureExploredAreaStatsInitialized(db)""", """    private fun insertRevealCells(insertCell: SQLiteStatement, point: TrackPoint, radiusMeters: Double): Double {""")
    s=replace(s, """        val insertCell: SQLiteStatement = db.compileStatement(
            "INSERT OR IGNORE INTO explored_cells(cell_x, cell_y) VALUES(?,?)"
        )
        var newlyExploredArea = 0.0
        try {
            for (dy in -yRange..yRange) for (dx in -xRange..xRange) {
                val east = dx * CELL_METERS * cosLat
                val north = dy * CELL_METERS
                if (east * east + north * north <= expanded * expanded) {
                    val cellY = centerY + dy
                    insertCell.bindLong(1, (centerX + dx).toLong())
                    insertCell.bindLong(2, cellY.toLong())
                    // SQLite returns -1 for INSERT OR IGNORE when this cell already exists.
                    if (insertCell.executeInsert() != -1L) {
                        newlyExploredArea += TrackMath.exploredCellAreaSquareMeters(cellY, CELL_METERS)
                    }
                    insertCell.clearBindings()
                }
            }
        } finally {
            insertCell.close()
        }
        if (newlyExploredArea > 0.0) {""", """        var newlyExploredArea = 0.0
        for (dy in -yRange..yRange) for (dx in -xRange..xRange) {
            val east = dx * CELL_METERS * cosLat
            val north = dy * CELL_METERS
            if (east * east + north * north <= expanded * expanded) {
                val cellY = centerY + dy
                // Both placeholders are assigned for every insert; no per-row allocation.
                insertCell.bindLong(1, (centerX + dx).toLong())
                insertCell.bindLong(2, cellY.toLong())
                if (insertCell.executeInsert() != -1L) {
                    newlyExploredArea += TrackMath.exploredCellAreaSquareMeters(cellY, CELL_METERS)
                }
            }
        }
        return newlyExploredArea
    }

    private fun addRevealedArea(db: SQLiteDatabase, newlyExploredArea: Double) {
        if (newlyExploredArea > 0.0) {""")
    s=replace(s, """            insertPointAndUpdateStats(db, point)
            db.setTransactionSuccessful()""", """            ensureDistanceStatsInitialized(db)
            insertPointAndUpdateStats(db, point, readLastPoint(db))
            db.setTransactionSuccessful()""")
    s=replace(s, """            val previous = readLastPoint(db)
            insertPointAndUpdateStats(db, point)
            ensureExploredAreaStatsInitialized(db)""", """            val previous = readLastPoint(db)
            insertPointAndUpdateStats(db, point, previous)
            ensureExploredAreaStatsInitialized(db)""")
    s=replace(s, """    private fun insertPointAndUpdateStats(db: SQLiteDatabase, point: TrackPoint) {
        ensureDistanceStatsInitialized(db)
        val previous = readLastPoint(db)""", """    private fun insertPointAndUpdateStats(db: SQLiteDatabase, point: TrackPoint, previous: TrackPoint?) {""")
    return s

mutate(src/"TrackStore.kt", store_edit)

def badge_edit(s):
    s=replace(s, """import java.text.SimpleDateFormat
import java.util.Date""", """import java.time.LocalDate
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit""")
    a=s.index("    // Called on the location service")
    b=s.index("    fun badges(",a)
    return s[:a]+'''    // Country lookup is optional, can involve a network request, and must never
    // delay durable GPS recording. At most one active and one latest pending lookup.
    private val countryWorker = ThreadPoolExecutor(
        1, 1, 30L, TimeUnit.SECONDS, ArrayBlockingQueue<Runnable>(1),
        { runnable -> Thread(runnable, "my-earth-country-badge").apply { isDaemon = true } },
        ThreadPoolExecutor.DiscardOldestPolicy()
    ).apply { allowCoreThreadTimeOut(true) }
    private var lastCountryRequestLat = Double.NaN
    private var lastCountryRequestLon = Double.NaN

    @Synchronized fun recordLocation(context: Context, lat: Double, lon: Double) {
        val app = context.applicationContext
        val p = prefs(app)
        val region = "${floor(lat * 10).toInt()}:${floor(lon * 10).toInt()}"
        val day = LocalDate.now().toString()
        val regions = p.getStringSet("regions", emptySet()) ?: emptySet()
        val days = p.getStringSet("days", emptySet()) ?: emptySet()
        // Copy the sets only when a new region/day is actually visited.
        if (region !in regions || day !in days) {
            val edit = p.edit()
            if (region !in regions) edit.putStringSet("regions", regions + region)
            if (day !in days) edit.putStringSet("days", days + day)
            edit.apply()
        }
        val oldLat = if (lastCountryRequestLat.isFinite()) lastCountryRequestLat
            else p.getFloat("country_check_lat", Float.NaN).toDouble()
        val oldLon = if (lastCountryRequestLon.isFinite()) lastCountryRequestLon
            else p.getFloat("country_check_lon", Float.NaN).toDouble()
        val moved = if (!oldLat.isFinite() || !oldLon.isFinite()) Double.POSITIVE_INFINITY
            else TrackMath.haversineMeters(oldLat, oldLon, lat, lon)
        if (moved >= 1000.0) {
            lastCountryRequestLat = lat
            lastCountryRequestLon = lon
            countryWorker.execute {
                // Only persist the attempted coordinates when a lookup actually starts.
                p.edit().putFloat("country_check_lat", lat.toFloat()).putFloat("country_check_lon", lon.toFloat()).apply()
                try {
                    if (Geocoder.isPresent()) {
                        @Suppress("DEPRECATION")
                        val code = Geocoder(app, Locale.ENGLISH).getFromLocation(lat, lon, 1)
                            ?.firstOrNull()?.countryCode?.uppercase(Locale.ROOT)
                        if (!code.isNullOrBlank()) {
                            val countries = p.getStringSet("countries", emptySet()) ?: emptySet()
                            val edit = p.edit()
                            if (p.getString("home_country", null) == null) edit.putString("home_country", code)
                            if (code !in countries) edit.putStringSet("countries", countries + code)
                            edit.apply()
                        }
                    }
                } catch (_: Exception) { /* Country badges are best-effort while offline. */ }
            }
        }
    }

'''+s[b:]
mutate(src/"BadgeManager.kt", badge_edit)

def service_edit(s):
    s=replace(s, """                                BadgeManager.recordLocation(this@LocationTrackingService, loc.latitude, loc.longitude)
                                lastSaved = loc""", """                                // Update the GPS baseline immediately after SQLite commits.
                                // Optional badge errors must not invalidate a saved fix.
                                lastSaved = loc
                                try {
                                    BadgeManager.recordLocation(applicationContext, loc.latitude, loc.longitude)
                                } catch (_: Exception) { /* Preserve GPS records if badges fail. */ }""")
    s=replace(s, """    // Keep 5-second high-accuracy fixes while moving. After three still samples,
    // reduce requests to 15 seconds; the first detected movement restores fast mode.""","""    // Keep the existing 3-second moving / 7-second still high-accuracy policy.
    // Restore fast mode on the first detected movement.""")
    s=replace(s, """        // The 15-second interval already reduces stationary GPS polling.""","""        // The 7-second interval already reduces stationary GPS polling.""")
    # A failed DB read at startup must not crash the app or bypass deduplication;
    # retry before processing the next accepted GPS fix.
    s=replace(s, "    private var lastSaved: android.location.Location? = null",
        "    private var lastSaved: android.location.Location? = null\n    private var baselineLoaded = false")
    a=s.index("        persistenceExecutor.execute {\n            store.lastPoint()")
    b=s.index("        createChannel()", a)
    s=s[:a]+"""        persistenceExecutor.execute { loadBaselineIfNeeded() }
"""+s[b:]
    s=replace(s, """                            val previous = lastSaved""", """                            if (!loadBaselineIfNeeded()) return@execute
                            val previous = lastSaved""")
    s=replace(s, """    private fun updateAdaptiveTrackingMode(location: android.location.Location) {""", """    // Only called on the serialized persistence worker.
    private fun loadBaselineIfNeeded(): Boolean {
        if (baselineLoaded) return true
        return try {
            store.lastPoint()?.let { saved ->
                lastSaved = android.location.Location("earth-unlock-db").apply {
                    latitude = saved.lat
                    longitude = saved.lon
                    accuracy = saved.accuracy
                    time = saved.time
                }
            }
            baselineLoaded = true
            true
        } catch (_: Exception) {
            // Retry on the next accepted fix, rather than trusting an empty baseline.
            false
        }
    }

    private fun updateAdaptiveTrackingMode(location: android.location.Location) {""")
    return s
mutate(src/"LocationTrackingService.kt", service_edit)

for p in [root/"app/build.gradle.kts",root/"scripts/verify-play-release-policy.py"]:
    mutate(p, lambda s: replace(replace(s, "versionCode = 101", "versionCode = 102"), 'versionName = "0.10.48"', 'versionName = "0.10.49"'))

# Android's instrumentation suite is a separate APK, NOT part of the Play AAB.
p=root/"app/build.gradle.kts"
mutate(p, lambda s: replace(replace(replace(s,'versionName = "0.10.49"','versionName = "0.10.49"\n        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"'),
    "    signingConfigs {", '    testBuildType = "release"\n    signingConfigs {'),
    '    testImplementation("junit:junit:4.13.2")','    testImplementation("junit:junit:4.13.2")\n    androidTestImplementation("androidx.test:runner:1.6.2")\n    androidTestImplementation("androidx.test.ext:junit:1.2.1")'))
print("v0.10.49: reuse per-fix SQL, stream legacy distance, isolate country lookups from GPS.")

test_dir = root/"app/src/androidTest/java/com/earthunlock/app"
test_dir.mkdir(parents=True, exist_ok=True)
(test_dir/"TrackingStorageInstrumentedTest.kt").write_text(
    Path(__file__).with_name("TrackingStorageInstrumentedTest.kt").read_text(encoding="utf-8"), encoding="utf-8")
