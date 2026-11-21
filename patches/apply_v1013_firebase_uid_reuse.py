from pathlib import Path
import re, sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

pattern = re.compile(r"    fun requestSyncIfEnabled\(context: Context, store: TrackStore, force: Boolean = false\) \{.*?(?=    private fun encode\()", re.S)
replacement = r'''    fun requestSyncIfEnabled(context: Context, store: TrackStore, force: Boolean = false) {
        if (!isEnabled(context)) return
        val now = SystemClock.elapsedRealtime()
        if (!force && now - lastSyncAt < MIN_SYNC_INTERVAL_MS) return
        if (!busy.compareAndSet(false, true)) return
        lastSyncAt = now

        try {
            val auth = FirebaseAuth.getInstance()
            val existingUser = auth.currentUser
            if (existingUser != null) {
                // Reuse the same Firebase UID; never create a fresh anonymous account per sync.
                syncForUid(existingUser.uid, store)
            } else {
                auth.signInAnonymously()
                    .addOnSuccessListener { result ->
                        val uid = result.user?.uid
                        if (uid.isNullOrBlank()) busy.set(false)
                        else syncForUid(uid, store)
                    }
                    .addOnFailureListener { busy.set(false) }
            }
        } catch (_: Exception) {
            busy.set(false)
        }
    }

    private fun syncForUid(uid: String, store: TrackStore) {
        if (uid.isBlank()) {
            busy.set(false)
            return
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

'''
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit("Firebase sync function block not found exactly once")
manager.write_text(s2, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 65' not in g or 'versionName = "0.10.12"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 65', 'versionCode = 66', 1).replace('versionName = "0.10.12"', 'versionName = "0.10.13"', 1)
gradle.write_text(g, encoding="utf-8")

print("Updated Firebase sync to reuse the existing authenticated UID; bumped to v0.10.13.")
