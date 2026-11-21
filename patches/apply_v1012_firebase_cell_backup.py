from pathlib import Path
import re, sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
store = pkg / "TrackStore.kt"
s = store.read_text(encoding="utf-8")

anchor = "    /** Read only the newest persisted fix; never load the full history during app startup. */"
if anchor not in s:
    raise SystemExit("TrackStore insertion point missing")
methods = r'''
    /** Export only revealed 5 m grid identifiers; GPS points are never included. */
    @Synchronized fun exportExploredCells(): List<Pair<Long, Long>> {
        val result = ArrayList<Pair<Long, Long>>()
        readableDatabase.rawQuery(
            "SELECT cell_x, cell_y FROM explored_cells ORDER BY cell_x, cell_y", null
        ).use { c ->
            while (c.moveToNext()) result.add(c.getLong(0) to c.getLong(1))
        }
        return result
    }

    /** Merge cloud cells into local SQLite without replacing or deleting local records. */
    @Synchronized fun mergeExploredCells(cells: List<Pair<Long, Long>>): Int {
        if (cells.isEmpty()) return 0
        val db = writableDatabase
        db.beginTransaction()
        var inserted = 0
        try {
            ensureExploredAreaStatsInitialized(db)
            val statement = db.compileStatement(
                "INSERT OR IGNORE INTO explored_cells(cell_x, cell_y) VALUES(?,?)"
            )
            var addedArea = 0.0
            try {
                for ((x, y) in cells) {
                    statement.bindLong(1, x)
                    statement.bindLong(2, y)
                    if (statement.executeInsert() != -1L) {
                        inserted++
                        addedArea += TrackMath.exploredCellAreaSquareMeters(y.toInt(), CELL_METERS)
                    }
                    statement.clearBindings()
                }
            } finally {
                statement.close()
            }
            if (addedArea > 0.0) {
                db.execSQL(
                    "UPDATE app_stats SET explored_area_m2 = explored_area_m2 + ? WHERE _id = 1",
                    arrayOf(addedArea)
                )
            }
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
        return inserted
    }

'''
s = s.replace(anchor, methods + anchor, 1)
store.write_text(s, encoding="utf-8")

manager = pkg / "FirebaseBackupManager.kt"
manager.write_text(r'''package com.earthunlock.app

import android.content.Context
import android.os.SystemClock
import android.util.Base64
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FieldValue
import com.google.firebase.firestore.FirebaseFirestore
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import java.util.zip.GZIPInputStream
import java.util.zip.GZIPOutputStream

/**
 * Optional cloud backup for revealed 5 m grid-cell IDs only.
 * Raw GPS coordinates, timestamps, and route history are deliberately excluded.
 */
object FirebaseBackupManager {
    private const val PREFS = "my_earth_cloud_backup"
    private const val ENABLED = "enabled"
    private const val CHUNK_CELL_COUNT = 10000
    private const val MIN_SYNC_INTERVAL_MS = 5 * 60 * 1000L
    private val busy = AtomicBoolean(false)
    private val worker = Executors.newSingleThreadExecutor()
    @Volatile private var lastSyncAt = 0L

    fun isEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(ENABLED, false)

    fun setEnabled(context: Context, enabled: Boolean) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(ENABLED, enabled).apply()
    }

    fun requestSyncIfEnabled(context: Context, store: TrackStore, force: Boolean = false) {
        if (!isEnabled(context)) return
        val now = SystemClock.elapsedRealtime()
        if (!force && now - lastSyncAt < MIN_SYNC_INTERVAL_MS) return
        if (!busy.compareAndSet(false, true)) return
        lastSyncAt = now

        try {
            FirebaseAuth.getInstance().signInAnonymously()
                .addOnSuccessListener { result ->
                    val uid = result.user?.uid
                    if (uid.isNullOrBlank()) {
                        busy.set(false)
                        return@addOnSuccessListener
                    }
                    val chunks = FirebaseFirestore.getInstance()
                        .collection("exploration_backups").document(uid).collection("chunks")
                    chunks.get()
                        .addOnSuccessListener { snapshot ->
                            worker.execute {
                                try {
                                    val cloudCells = ArrayList<Pair<Long, Long>>()
                                    for (document in snapshot.documents) {
                                        val payload = document.getString("payload") ?: continue
                                        val version = document.getLong("formatVersion") ?: continue
                                        if (version != 1L) continue
                                        cloudCells.addAll(decode(payload))
                                    }
                                    // Restore first, then upload the union. Existing local data is never replaced.
                                    store.mergeExploredCells(cloudCells)
                                    val localCells = store.exportExploredCells()
                                    val writes = ArrayList<com.google.android.gms.tasks.Task<Void>>()
                                    var offset = 0
                                    var index = 0
                                    while (offset < localCells.size) {
                                        val end = minOf(offset + CHUNK_CELL_COUNT, localCells.size)
                                        val payload = encode(localCells.subList(offset, end))
                                        val data = hashMapOf<String, Any>(
                                            "formatVersion" to 1,
                                            "payload" to payload,
                                            "updatedAt" to FieldValue.serverTimestamp()
                                        )
                                        writes.add(chunks.document("cells_%06d".format(index)).set(data))
                                        offset = end
                                        index++
                                    }
                                    if (writes.isEmpty()) {
                                        // Empty local accounts do not create empty backup documents.
                                        busy.set(false)
                                    } else {
                                        com.google.android.gms.tasks.Tasks.whenAll(writes)
                                            .addOnCompleteListener { busy.set(false) }
                                    }
                                } catch (_: Exception) {
                                    busy.set(false)
                                }
                            }
                        }
                        .addOnFailureListener { busy.set(false) }
                }
                .addOnFailureListener { busy.set(false) }
        } catch (_: Exception) {
            busy.set(false)
        }
    }

    private fun encode(cells: List<Pair<Long, Long>>): String {
        val raw = buildString {
            for ((x, y) in cells) append(x).append(',').append(y).append('\n')
        }.toByteArray(Charsets.UTF_8)
        val bytes = ByteArrayOutputStream().use { output ->
            GZIPOutputStream(output).use { it.write(raw) }
            output.toByteArray()
        }
        return Base64.encodeToString(bytes, Base64.NO_WRAP)
    }

    private fun decode(payload: String): List<Pair<Long, Long>> {
        val compressed = Base64.decode(payload, Base64.NO_WRAP)
        val raw = GZIPInputStream(ByteArrayInputStream(compressed)).bufferedReader(Charsets.UTF_8).use { it.readLines() }
        val result = ArrayList<Pair<Long, Long>>(raw.size)
        for (line in raw) {
            val comma = line.indexOf(',')
            if (comma <= 0 || comma == line.lastIndex) continue
            val x = line.substring(0, comma).toLongOrNull() ?: continue
            val y = line.substring(comma + 1).toLongOrNull() ?: continue
            result.add(x to y)
        }
        return result
    }
}
''', encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'firebase-bom' not in g:
    g = g.replace('dependencies {', '''dependencies {
    implementation(platform("com.google.firebase:firebase-bom:33.7.0"))
    implementation("com.google.firebase:firebase-auth")
    implementation("com.google.firebase:firebase-firestore")''', 1)
gradle.write_text(g, encoding="utf-8")

activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
# Add a persistent, explicit opt-in control to the existing settings panel.
if "MY_EARTH_CLOUD_BACKUP_BUTTON" not in a:
    marker = "        setContentView(root)"
    if marker not in a:
        raise SystemExit("MainActivity setContentView insertion point missing")
    block = r'''
        // MY_EARTH_CLOUD_BACKUP_BUTTON: cloud backup is opt-in and never starts silently.
        val cloudBackupButton = Button(this).apply {
            text = if (FirebaseBackupManager.isEnabled(this@MainActivity)) "☁  클라우드 백업 사용 중" else "☁  클라우드 백업 설정"
            isAllCaps = false
            setOnClickListener {
                if (FirebaseBackupManager.isEnabled(this@MainActivity)) {
                    AlertDialog.Builder(this@MainActivity)
                        .setTitle("클라우드 백업")
                        .setMessage("해금된 지도 셀만 Firebase에 백업합니다. GPS 좌표와 시간순 이동 경로는 전송하지 않습니다.")
                        .setNegativeButton("백업 끄기") { _, _ ->
                            FirebaseBackupManager.setEnabled(this@MainActivity, false)
                            text = "☁  클라우드 백업 설정"
                        }
                        .setPositiveButton("지금 백업") { _, _ ->
                            FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true)
                        }
                        .setNeutralButton("닫기", null)
                        .show()
                } else {
                    AlertDialog.Builder(this@MainActivity)
                        .setTitle("탐험 기록 클라우드 백업")
                        .setMessage("동의하면 해금된 지도 셀 식별자만 Firebase에 백업됩니다. GPS 좌표, 이동 경로, 위치 기록과 시간 정보는 업로드하지 않습니다. 백업은 Google 계정 연결 전까지 현재 앱 설치의 익명 계정에 연결됩니다. 앱 데이터 삭제나 기기 변경 전에 Google 계정 복구 기능을 연결해야 합니다.")
                        .setNegativeButton("나중에", null)
                        .setPositiveButton("동의하고 켜기") { _, _ ->
                            FirebaseBackupManager.setEnabled(this@MainActivity, true)
                            text = "☁  클라우드 백업 사용 중"
                            FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true)
                        }
                        .show()
                }
            }
        }
        panel.addView(cloudBackupButton, LinearLayout.LayoutParams(-1, -2))
'''
    a = a.replace(marker, block + "\n" + marker, 1)
# Sync on launch/resume and after active tracking broadcasts; manager throttles repeated requests.
if "FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store)" not in a:
    a = a.replace("            refreshFog()\n            val lat = intent?", "            refreshFog()\n            FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store)\n            val lat = intent?", 1)
    a = a.replace("        refreshTrackingStatus()\n        refreshFog()\n    }\n\n    private fun requestAndStart()", "        refreshTrackingStatus()\n        refreshFog()\n        FirebaseBackupManager.requestSyncIfEnabled(this, store)\n    }\n\n    private fun requestAndStart()", 1)
    a = a.replace("        refreshLatestSavedPosition()\n        refreshFog()\n        refreshTrackingStatus()", "        refreshLatestSavedPosition()\n        refreshFog()\n        refreshTrackingStatus()\n        FirebaseBackupManager.requestSyncIfEnabled(this, store)", 1)
activity.write_text(a, encoding="utf-8")

# Bump app version without changing the signing identity or package ID.
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 64' not in g or 'versionName = "0.10.11"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 64', 'versionCode = 65', 1).replace('versionName = "0.10.11"', 'versionName = "0.10.12"', 1)
gradle.write_text(g, encoding="utf-8")

print("Added opt-in Firebase anonymous auth and Firestore backup/restore for revealed 5 m cells only.")
