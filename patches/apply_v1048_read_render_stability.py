"""v0.10.48: bounded viewport refresh and lower-allocation rendering/read-only stats."""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv)>1 else "source")
src = root / "app/src/main/java/com/earthunlock/app"
activity = src / "MainActivity.kt"
s = activity.read_text(encoding="utf-8")
original = s

def once(old, new):
    global s
    assert s.count(old)==1, f"Anchor mismatch: {old[:100]}"
    s=s.replace(old,new,1)
def block(start,end,new):
    global s
    a=s.index(start); b=s.index(end,a)
    s=s[:a]+new+s[b:]

# Only the newest viewport is retained while a single DB query is running.
once("    private val refreshGeneration = AtomicInteger(0)", """    private val refreshGeneration = AtomicInteger(0)
    private data class FogRequest(
        val generation: Int, val north: Double, val east: Double,
        val south: Double, val west: Double, val zoom: Double
    )
    private val fogRequests = LatestWorkQueue<FogRequest>()
    private var fogKickScheduled = false
    private var badgeRefreshInFlight = false
    private var badgeDialogLoading = false
    private val fogRefreshKick = Runnable {
        fogKickScheduled = false
        dispatchFogRequest()
    }""")
once("""        val badgeList = BadgeManager.badges(this, store)
        val badgeUnlockedCount = badgeList.count { it.unlocked }
        val badgesButton = Button(this).apply {
            text = "🏅 배지 " + badgeUnlockedCount + "/" + badgeList.size""","""        val badgesButton = Button(this).apply {
            text = "🏅 배지" """.rstrip())
once('            contentDescription = "나의 배지 컬렉션, " + badgeUnlockedCount + "개 획득"','            contentDescription = "나의 배지 컬렉션"')
block("    private fun refreshBadgeCount(force: Boolean = false) {","        val unlocked = badges.count { it.unlocked }\n        val root = LinearLayout(this).apply {", """    private fun refreshBadgeCount(force: Boolean = false) {
        val button = badgeCountButton ?: return
        if (activityShuttingDown.get() || badgeRefreshInFlight) return
        val now = android.os.SystemClock.elapsedRealtime()
        if (!force && now - lastBadgeCountRefreshAt < 10_000L) return
        lastBadgeCountRefreshAt = now
        badgeRefreshInFlight = true
        try {
            refreshExecutor.execute {
                val badges = try { BadgeManager.badges(applicationContext, store) } catch (_: Exception) { null }
                runOnUiThread {
                    badgeRefreshInFlight = false
                    if (badges != null && !activityShuttingDown.get() && !isFinishing && !isDestroyed) {
                        val unlocked = badges.count { it.unlocked }
                        if (button.text.toString() != "🏅 배지 $unlocked/${badges.size}") {
                            button.text = "🏅 배지 $unlocked/${badges.size}"
                            button.contentDescription = "나의 배지 컬렉션, ${unlocked}개 획득"
                        }
                    }
                }
            }
        } catch (_: RejectedExecutionException) {
            badgeRefreshInFlight = false
        }
    }

    private fun showBadges() {
        if (activityShuttingDown.get() || badgeDialogLoading) return
        badgeDialogLoading = true
        try {
            refreshExecutor.execute {
                val badges = try { BadgeManager.badges(applicationContext, store) } catch (_: Exception) { null }
                runOnUiThread {
                    badgeDialogLoading = false
                    if (activityShuttingDown.get() || isFinishing || isDestroyed || !receiverRegistered) return@runOnUiThread
                    if (badges != null) showBadgeDialog(badges)
                    else Toast.makeText(this, R.string.dashboard_badge_load_failed, Toast.LENGTH_SHORT).show()
                }
            }
        } catch (_: RejectedExecutionException) {
            badgeDialogLoading = false
        }
    }

    private fun showBadgeDialog(badges: List<ExplorerBadge>) {
""")
block("    private fun refreshFog() {","    private fun refreshTrackingStatus() {", """    private fun refreshFog() {
        if (!::map.isInitialized || !::fog.isInitialized || !receiverRegistered || activityShuttingDown.get() || isFinishing || isDestroyed) return
        val bounds = map.boundingBox
        fogRequests.offer(FogRequest(
            refreshGeneration.incrementAndGet(),
            bounds.latNorth, bounds.lonEast, bounds.latSouth, bounds.lonWest, map.zoomLevelDouble
        ))
        scheduleFogRequest()
    }

    // Coalesce rapid gestures without a growing executor queue, and still run
    // the latest request when movement stops. All queue operations are UI-thread only.
    private fun scheduleFogRequest() {
        if (!receiverRegistered || activityShuttingDown.get() || fogKickScheduled || fogRequests.isRunning || !fogRequests.hasPending) return
        fogKickScheduled = true
        dashboardHandler.postDelayed(fogRefreshKick, 40L)
    }

    private fun dispatchFogRequest() {
        if (!receiverRegistered || activityShuttingDown.get() || isFinishing || isDestroyed) return
        val request = fogRequests.startNext() ?: return
        try {
            refreshExecutor.execute {
                val result = try {
                    val aggregationFactor = TrackMath.fogAggregationFactor(request.zoom)
                    val visibleCells = store.visibleCells(
                        request.north, request.east, request.south, request.west,
                        limit = 25000, aggregationFactor = aggregationFactor
                    )
                    visibleCells to store.exploredAreaSquareMeters()
                } catch (_: Exception) { null }
                runOnUiThread {
                    fogRequests.finish()
                    if (activityShuttingDown.get() || isFinishing || isDestroyed) return@runOnUiThread
                    // Never display an outdated viewport after a newer map gesture.
                    if (request.generation == refreshGeneration.get()) {
                        if (result != null) {
                            val (visibleCells, area) = result
                            fog.update(visibleCells)
                            val earthSurfaceAreaM2 = 4.0 * Math.PI * TrackMath.EARTH_RADIUS_METERS * TrackMath.EARTH_RADIUS_METERS
                            val explorationPercent = (area / earthSurfaceAreaM2) * 100.0
                            val areaLabel = if (area >= 1_000_000.0)
                                String.format(Locale.getDefault(), "%.3f km²", area / 1_000_000.0)
                            else String.format(Locale.getDefault(), "%,.0f m²", area)
                            val percentLabel = String.format(Locale.US, "%.8f%%", explorationPercent)
                            if (countText.text.toString() != areaLabel) {
                                countText.text = areaLabel
                                countText.contentDescription = getString(R.string.dashboard_area_accessibility, areaLabel)
                            }
                            val percent = getString(R.string.dashboard_earth_percent, percentLabel)
                            if (percentText.text.toString() != percent) percentText.text = percent
                            refreshTrackingStatus()
                        } else {
                            percentText.text = getString(R.string.map_load_failed)
                        }
                    }
                    scheduleFogRequest()
                }
            }
        } catch (_: RejectedExecutionException) {
            fogRequests.finish()
            fogRequests.clearPending()
        }
    }

    private fun cancelPendingFogRefresh() {
        dashboardHandler.removeCallbacks(fogRefreshKick)
        fogKickScheduled = false
        fogRequests.clearPending()
        refreshGeneration.incrementAndGet()
    }

""")
once("""        recordActionButton.isEnabled = !pending
        recordActionButton.alpha = if (pending) 0.7f else 1f""","""        if (recordActionButton.isEnabled == pending) recordActionButton.isEnabled = !pending
        val alpha = if (pending) 0.7f else 1f
        if (recordActionButton.alpha != alpha) recordActionButton.alpha = alpha""")
once("""    override fun onStop() {
        dashboardHandler.removeCallbacks(dashboardStatusPoll)""","""    override fun onStop() {
        dashboardHandler.removeCallbacks(dashboardStatusPoll)
        cancelPendingFogRefresh()""")
once("""        activityShuttingDown.set(true)
        // Invalidate pending UI callbacks""","""        activityShuttingDown.set(true)
        cancelPendingFogRefresh()
        // Invalidate pending UI callbacks""")
# Keep permissions, authentication, backup, location controls, and map setup intact.
def section(t,start,end):
    a=t.index(start); return t[a:t.index(end,a)]
for start,end in [
    ("        val accountBackupButton = Button(this).apply {","        accountToolsColumn.addView(accountBackupButton"),
    ("    private fun confirmCloudBackupOptIn()","    private fun refreshBadgeCount("),
    ("    override fun onActivityResult(","    private fun confirmAccountDeletion()"),
    ("    private fun goToCurrentLocation()","    override fun onStart()")
]:
    assert section(original,start,end)==section(s,start,end),start
activity.write_text(s,encoding="utf-8")

# A read of an already initialized aggregate should never start a writer transaction.
store=src / "TrackStore.kt"
s=store.read_text(encoding="utf-8")
once('    @Synchronized fun exploredCellCount(): Long =', '''    /** First-footstep badge only needs existence, not a full-table count. */
    @Synchronized fun hasExploredCells(): Boolean = readableDatabase.rawQuery(
        "SELECT EXISTS(SELECT 1 FROM explored_cells)", null
    ).use { it.moveToFirst() && it.getInt(0) != 0 }

    @Synchronized fun exploredCellCount(): Long =''')
once("""    @Synchronized fun exploredAreaSquareMeters(): Double {
        val db = writableDatabase""","""    @Synchronized fun exploredAreaSquareMeters(): Double {
        val current = readableDatabase.rawQuery(
            "SELECT explored_area_m2 FROM app_stats WHERE _id = 1", null
        ).use { if (it.moveToFirst() && !it.isNull(0)) it.getDouble(0) else null }
        if (current != null) return current

        // Legacy stores may need the existing one-time transactional backfill.
        val db = writableDatabase""")
store.write_text(s,encoding="utf-8")
badge=src / "BadgeManager.kt"
s=badge.read_text(encoding="utf-8")
once("val explored = store.exploredCellCount() > 0","val explored = store.hasExploredCells()")
badge.write_text(s,encoding="utf-8")

# Same projection, colors, overscan and radius. Only reusable draw objects.
fog=src / "FogOverlay.kt"
s=fog.read_text(encoding="utf-8")
block("    private val fogPaint =", "    /** Called after a pan/zoom", """    private val fogFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(225, 10, 20, 36)
        style = Paint.Style.FILL
    }
    private val erasePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        xfermode = android.graphics.PorterDuffXfermode(android.graphics.PorterDuff.Mode.DST_OUT)
    }
    private val center = Point()
    private val edge = Point()
    private val scratchPoint = GeoPoint(0.0, 0.0)

""")
block("        cells = newCells\n", "    override fun draw(", """        cells = newCells
        map.invalidate()
    }

    fun release() { cells = emptyList() }

    /** A pan/zoom changes the projection even when the queried cell IDs are unchanged. */
    fun invalidateViewport() = map.invalidate()

""")
once("""        val fogFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = fogColor
            style = Paint.Style.FILL
        }
""","")
once("""        val center = Point()
        val edge = Point()
""","")
once("            projection.toPixels(GeoPoint(lat, lon), center)","            scratchPoint.setCoords(lat, lon)\n            projection.toPixels(scratchPoint, center)")
once("            projection.toPixels(GeoPoint(northLat, lon), edge)","            scratchPoint.setCoords(northLat, lon)\n            projection.toPixels(scratchPoint, edge)")
s=s.replace("import android.graphics.Bitmap\n","").replace(" * The viewport mask is rasterized once and reused until the map viewport/data changes.\n"," * Draw uses reusable objects and the map's current projection.\n")
fog.write_text(s,encoding="utf-8")

q=src / "LatestWorkQueue.kt"
assert not q.exists()
q.write_text('''package com.earthunlock.app

/** Main-thread mailbox: one running request and at most one latest pending value. */
internal class LatestWorkQueue<T : Any> {
    private var pending: T? = null
    var isRunning: Boolean = false
        private set
    val hasPending: Boolean get() = pending != null

    fun offer(value: T) { pending = value }
    fun startNext(): T? {
        if (isRunning) return null
        val next = pending ?: return null
        pending = null
        isRunning = true
        return next
    }
    fun finish() { isRunning = false }
    fun clearPending() { pending = null }
}
''',encoding="utf-8")
test=root/"app/src/test/java/com/earthunlock/app/LatestWorkQueueTest.kt"
test.write_text('''package com.earthunlock.app

import org.junit.Assert.*
import org.junit.Test

class LatestWorkQueueTest {
    @Test fun rapidOffersKeepOnlyLatest() {
        val queue = LatestWorkQueue<Int>()
        repeat(10000) { queue.offer(it) }
        assertEquals(9999, queue.startNext() ?: -1)
        assertFalse(queue.hasPending)
        assertTrue(queue.isRunning)
        queue.finish()
        assertNull(queue.startNext())
    }
    @Test fun oneRunningAndOneLatestPending() {
        val queue = LatestWorkQueue<String>()
        queue.offer("first")
        assertEquals("first", queue.startNext())
        queue.offer("obsolete")
        queue.offer("current")
        assertNull(queue.startNext())
        assertTrue(queue.hasPending)
        queue.finish()
        assertEquals("current", queue.startNext())
        queue.finish()
        assertNull(queue.startNext())
    }
    @Test fun lifecycleClearDropsPendingButDoesNotCreateParallelWork() {
        val queue = LatestWorkQueue<Int>()
        queue.offer(1)
        assertEquals(1, queue.startNext() ?: -1)
        queue.offer(2)
        queue.clearPending()
        queue.offer(3)
        assertNull(queue.startNext())
        queue.finish()
        assertEquals(3, queue.startNext() ?: -1)
    }
}
''',encoding="utf-8")
for folder,value in [("values","Could not load your badges."),("values-ko","배지 기록을 불러오지 못했습니다.")]:
    p=root/f"app/src/main/res/{folder}/strings.xml"
    xml=p.read_text(encoding="utf-8")
    assert xml.count("</resources>")==1
    p.write_text(xml.replace("</resources>",f'    <string name="dashboard_badge_load_failed">{value}</string>\n</resources>'),encoding="utf-8")
for p in [root/"app/build.gradle.kts",root/"scripts/verify-play-release-policy.py"]:
    s=p.read_text(encoding="utf-8")
    once("versionCode = 100","versionCode = 101")
    once('versionName = "0.10.47"','versionName = "0.10.48"')
    p.write_text(s,encoding="utf-8")
print("v0.10.48 applied: bounded viewport queue, async badges, read-only cached area, draw object reuse.")
