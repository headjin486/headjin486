from pathlib import Path
import re, sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")
start = s.find("    fun requestSyncIfEnabled(")
end = s.find("    private fun encode(", start)
if start < 0 or end < 0:
    raise SystemExit("Firebase sync methods not found; refusing unsafe patch")

replacement = r'''    fun requestSyncIfEnabled(
        context: Context,
        store: TrackStore,
        force: Boolean = false,
        onStatus: (String) -> Unit = {}
    ) {
        if (!isEnabled(context)) {
            onStatus("클라우드 백업이 꺼져 있습니다.")
            return
        }
        val now = SystemClock.elapsedRealtime()
        if (!force && now - lastSyncAt < MIN_SYNC_INTERVAL_MS) {
            onStatus("최근 백업 이후 5분이 지나지 않아 자동 백업을 건너뛰었습니다.")
            return
        }
        if (!busy.compareAndSet(false, true)) {
            onStatus("이미 클라우드 백업이 진행 중입니다.")
            return
        }
        lastSyncAt = now
        onStatus("백업 시작: Google 계정 인증 확인 중…")
        try {
            val auth = FirebaseAuth.getInstance()
            val existingUser = auth.currentUser
            if (existingUser != null) {
                syncForUid(existingUser.uid, store, onStatus)
            } else {
                auth.signInAnonymously()
                    .addOnSuccessListener { result ->
                        val uid = result.user?.uid
                        if (uid.isNullOrBlank()) {
                            busy.set(false)
                            onStatus("백업 실패: Firebase 사용자 인증 정보를 확인할 수 없습니다.")
                        } else syncForUid(uid, store, onStatus)
                    }
                    .addOnFailureListener { error ->
                        busy.set(false)
                        onStatus("백업 실패: Firebase 인증 오류 - \${error.localizedMessage ?: "알 수 없는 오류"}")
                    }
            }
        } catch (error: Exception) {
            busy.set(false)
            onStatus("백업 실패: \${error.localizedMessage ?: error.javaClass.simpleName}")
        }
    }

    private fun syncForUid(uid: String, store: TrackStore, onStatus: (String) -> Unit) {
        if (uid.isBlank()) {
            busy.set(false)
            onStatus("백업 실패: 계정 식별자가 비어 있습니다.")
            return
        }
        onStatus("기존 클라우드 기록 확인 중…")
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
                        onStatus("기존 기록 \${cloudCells.size}개 확인. 휴대폰 기록과 병합 중…")
                        val restored = store.mergeExploredCells(cloudCells)
                        val localCells = store.exportExploredCells()
                        onStatus("총 \${localCells.size}개 지도 기록을 클라우드에 저장 중…")
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
                            onStatus("백업 완료: 저장할 해금 지도 기록이 없습니다. 기존 기록 \${cloudCells.size}개를 확인했습니다.")
                        } else {
                            com.google.android.gms.tasks.Tasks.whenAll(writes)
                                .addOnCompleteListener { task ->
                                    busy.set(false)
                                    if (task.isSuccessful) {
                                        onStatus("백업 완료: 지도 기록 \${localCells.size}개 저장. 클라우드 기록 \${cloudCells.size}개 중 \${restored}개를 새로 복원했습니다.")
                                    } else {
                                        val error = task.exception
                                        onStatus("백업 실패: 클라우드 저장 오류 - \${error?.localizedMessage ?: "네트워크 또는 Firestore 규칙을 확인하세요."}")
                                    }
                                }
                        }
                    } catch (error: Exception) {
                        busy.set(false)
                        onStatus("백업 실패: 기록 처리 오류 - \${error.localizedMessage ?: error.javaClass.simpleName}")
                    }
                }
            }
            .addOnFailureListener { error ->
                busy.set(false)
                onStatus("백업 실패: 클라우드 기록 조회 오류 - \${error.localizedMessage ?: "네트워크 또는 Firestore 규칙을 확인하세요."}")
            }
    }

'''
s = s[:start] + replacement + s[end:]
manager.write_text(s, encoding="utf-8")

activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
old = "FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true)"
new = '''FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true) { message ->
                                runOnUiThread {
                                    Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
                                }
                            }'''
if old not in a:
    raise SystemExit("Manual backup action not found; refusing to patch UI")
a = a.replace(old, new, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 68' not in g or 'versionName = "0.10.15"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 68', 'versionCode = 69', 1).replace('versionName = "0.10.15"', 'versionName = "0.10.16"', 1)
gradle.write_text(g, encoding="utf-8")
print("Added visible cloud-backup progress and detailed success/failure messages; bumped to v0.10.16.")
