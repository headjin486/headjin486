package com.earthunlock.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.security.MessageDigest

/** Run only on an isolated emulator. Seed the old signed app, then compare the real
 * database after an in-place update against a golden result produced by the old app. */
@RunWith(AndroidJUnit4::class)
class TrackingStorageInstrumentedTest {
    private val ctx get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val fixture get() = ctx.getSharedPreferences("upgrade_regression_fixture", 0)
    private val initial = listOf(
        TrackPoint(36.12, 128.34, 5f, 1700000000000L),
        TrackPoint(36.12009, 128.34, 5f, 1700000008000L),
        TrackPoint(36.12018, 128.34008, 5f, 1700000016000L)
    )
    private val continuation = listOf(
        // Vehicle-speed segment; many overlapping reveal circles.
        TrackPoint(36.12618, 128.34008, 6f, 1700000056000L),
        TrackPoint(36.12018, 128.34008, 5f, 1700000096000L),
        // Long gap: do not interpolate a path across the world.
        TrackPoint(0.001, 179.9998, 5f, 1700000400000L),
        TrackPoint(0.001, -179.9998, 5f, 1700000410000L),
        TrackPoint(80.0000, 10.0000, 5f, 1700000700000L),
        TrackPoint(80.00005, 10.0002, 5f, 1700000710000L)
    )
    private fun fingerprint(store: TrackStore): String {
        val digest = MessageDigest.getInstance("SHA-256")
        store.exportExploredCells().forEach { (x, y) ->
            digest.update("$x:$y\n".toByteArray(Charsets.UTF_8))
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
    private fun saveExpected(prefix: String, store: TrackStore) {
        assertTrue(store.exploredCellCount() > 0)
        assertTrue(fixture.edit()
            .putInt("${prefix}_points", store.count())
            .putLong("${prefix}_cells", store.exploredCellCount())
            .putString("${prefix}_hash", fingerprint(store))
            .putLong("${prefix}_area", store.exploredAreaSquareMeters().toBits())
            .putLong("${prefix}_distance", store.distanceMeters().toBits())
            .commit())
    }
    private fun verify(prefix: String, store: TrackStore) {
        assertEquals(fixture.getInt("${prefix}_points", -1), store.count())
        assertEquals(fixture.getLong("${prefix}_cells", -1), store.exploredCellCount())
        assertEquals(fixture.getString("${prefix}_hash", null), fingerprint(store))
        assertEquals(Double.fromBits(fixture.getLong("${prefix}_area", 0)), store.exploredAreaSquareMeters(), 0.00001)
        assertEquals(Double.fromBits(fixture.getLong("${prefix}_distance", 0)), store.distanceMeters(), 0.000001)
    }

    @Test fun seedBeforeUpgrade() {
        // This method is invoked against the signed 0.10.47 APK on a fresh emulator.
        assertEquals("0.10.47", ctx.packageManager.getPackageInfo(ctx.packageName, 0).versionName)
        TrackStore(ctx).use { store ->
            assertEquals("Emulator must have an empty GPS history", 0, store.count())
            (initial + continuation).forEach { store.recordAndReveal(it, 12.0) }
            saveExpected("full", store)
        }
        assertTrue(ctx.deleteDatabase("earth_explorer.db"))
        TrackStore(ctx).use { store ->
            initial.forEach { store.recordAndReveal(it, 12.0) }
            saveExpected("initial", store)
            assertEquals(initial.last(), store.lastPoint())
        }
    }
    @Test fun verifyAfterUpgrade() {
        assertEquals("0.10.49", ctx.packageManager.getPackageInfo(ctx.packageName, 0).versionName)
        TrackStore(ctx).use { store ->
            verify("initial", store)
            assertEquals(initial.last(), store.lastPoint())
            continuation.forEach { store.recordAndReveal(it, 12.0) }
            verify("full", store)
            assertEquals(continuation.last(), store.lastPoint())
            // Force legacy aggregate reconstruction; verify values again.
            store.writableDatabase.execSQL("UPDATE app_stats SET distance_meters=NULL, last_lat=NULL, last_lon=NULL, last_accuracy=NULL, last_time=NULL, explored_area_m2=NULL WHERE _id=1")
            verify("full", store)
            // Induce a SQLite failure mid-record, after the point insert.
            // Both the point and its cell/area transaction must roll back.
            store.writableDatabase.execSQL("CREATE TRIGGER regression_abort BEFORE INSERT ON explored_cells BEGIN SELECT RAISE(ABORT,'regression test'); END")
            try {
                val next = TrackPoint(80.00010, 10.00040, 5f, 1700000720000L)
                var failed = false
                try { store.recordAndReveal(next, 12.0) } catch (_: android.database.sqlite.SQLiteException) { failed = true }
                assertTrue("Expected injected write failure", failed)
            } finally {
                store.writableDatabase.execSQL("DROP TRIGGER regression_abort")
            }
            verify("full", store)
            assertEquals(continuation.last(), store.lastPoint())
        }
        // Reopen the DB independently to prove the committed records are durable.
        TrackStore(ctx).use { verify("full", it) }
    }
}
