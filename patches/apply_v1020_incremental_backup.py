from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

pattern = re.compile(
    r"    private fun syncForUid\\(.*?(?=    private fun encode\\()",
    re.S,
)
replacement = r'''    /**
     * Merge cloud and local cells, then upload only cells absent from the cloud.
     * Existing backup documents are immutable; each new delta chunk gets a
     * deterministic content-hash ID so a retry does not create duplicate chunks.
     */
    private fun syncForUid(uid: String, store: TrackStore, onStatus: (String) -> Unit) {
        if (uid.isBlank()) {
            busy.set(false)
            onStatus("백업 실패: 계정 식별자가 비어 있습니다.")
            return
        }
        val chunks = FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(uid).collection("chunks")
        onStatus("기존 클라우드 기록 확인 중…")
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

                        onStatus("기존 기록 ${cloudCells.size}개 확인. 휴대폰 기록과 병합 중…")
                        val restored = store.mergeExploredCells(cloudCells)
                        val localCells = store.exportExploredCells()
                        val cloudCellSet = cloudCells.toHashSet()
                        val missingCells = localCells.filterNot { cloudCellSet.contains(it) }
                        val existingDocumentIds = snapshot.documents.map { it.id }.toHashSet()

                        onStatus(
                            "전체 지도 기록 ${localCells.size}개 중 새 기록 ${missingCells.size}개만 클라우드에 추가 중…"
                        )

                        val writes = ArrayList<com.google.android.gms.tasks.Task<Void>>()
                        var offset = 0
                        while (offset < missingCells.size) {
                            val end = minOf(offset + CHUNK_CELL_COUNT, missingCells.size)
                            val payload = encode(missingCells.subList(offset, end))
                            val digest = java.security.MessageDigest.getInstance("SHA-256")
                                .digest(payload.toByteArray(Charsets.UTF_8))
                                .joinToString("") { "%02x".format(it) }
                            val documentId = "delta_${digest}"
                            if (!existingDocumentIds.contains(documentId)) {
                                val data = hashMapOf<String, Any>(
                                    "formatVersion" to 1,
                                    "payload" to payload,
                                    "updatedAt" to FieldValue.serverTimestamp()
                                )
                                writes.add(chunks.document(documentId).set(data))
                            }
                            offset = end
                        }

                        if (writes.isEmpty()) {
                            busy.set(false)
                            onStatus(
                                "백업 완료: 전체 지도 기록 ${localCells.size}개가 이미 클라우드와 동기화되어 있습니다. 새로 저장한 기록은 없습니다."
                            )
                        } else {
                            com.google.android.gms.tasks.Tasks.whenAll(writes)
                                .addOnCompleteListener { task ->
                                    busy.set(false)
                                    if (task.isSuccessful) {
                                        onStatus(
                                            "백업 완료: 전체 ${localCells.size}개 중 새 기록 ${missingCells.size}개만 추가 저장했습니다. 클라우드 기록 ${cloudCells.size}개 중 ${restored}개를 복원했습니다."
                                        )
                                    } else {
                                        val error = task.exception
                                        onStatus(
                                            "백업 실패: 클라우드 저장 오류 - ${error?.localizedMessage ?: error.toString()}"
                                        )
                                    }
                                }
                        }
                    } catch (error: Exception) {
                        busy.set(false)
                        onStatus("백업 실패: 기록 처리 오류 - ${error.localizedMessage ?: error.javaClass.simpleName}")
                    }
                }
            }
            .addOnFailureListener { error ->
                busy.set(false)
                onStatus("백업 실패: 클라우드 기록 조회 오류 - ${error.localizedMessage ?: error.toString()}")
            }
    }

'''
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit("Expected exactly one syncForUid block; refusing to modify backup implementation")
if 'versionCode = 72' not in (root / "app/build.gradle.kts").read_text(encoding="utf-8"):
    raise SystemExit("Unexpected app version; expected v0.10.19 before incremental-backup patch")
if 'delta_' not in s2 or 'missingCells' not in s2:
    raise SystemExit("Incremental backup implementation verification failed")
manager.write_text(s2, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
g = g.replace('versionCode = 72', 'versionCode = 73', 1)
g = g.replace('versionName = "0.10.19"', 'versionName = "0.10.20"', 1)
gradle.write_text(g, encoding="utf-8")

print("Implemented append-only incremental cloud backup; bumped to v0.10.20.")
