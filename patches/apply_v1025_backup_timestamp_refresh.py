from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

start = s.find("    fun getLastSuccessfulBackup(")
end = s.find("    private fun encode(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate backup timestamp reader")
reader = r"""
    /**
     * Read the last successful sync marker from the existing chunks subcollection.
     */
    fun getLastSuccessfulBackup(callback: (String) -> Unit) {
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            callback("아직 연결된 계정이 없습니다.")
            return
        }
        FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(user.uid)
            .collection("chunks").document("_backup_status").get()
            .addOnSuccessListener { document ->
                val stamp = document.getTimestamp("updatedAt")
                if (stamp == null) {
                    callback("아직 완료된 클라우드 백업 기록이 없습니다.")
                } else {
                    val formatter = java.text.SimpleDateFormat(
                        "yyyy.MM.dd HH:mm", java.util.Locale.getDefault()
                    )
                    formatter.timeZone = java.util.TimeZone.getDefault()
                    callback("마지막 정상 백업: " + formatter.format(stamp.toDate()))
                }
            }
            .addOnFailureListener {
                callback("마지막 백업 시각을 확인하지 못했습니다.")
            }
    }

"""
s = s[:start] + reader + s[end:]

pattern = re.compile(
    r"                        if \(writes\.isEmpty\(\)\) \{.*?\n                        \}\n                    \} catch \(error: Exception\)",
    re.S,
)
replacement = r"""                        val finishSuccessfulBackup: (String) -> Unit = { detail ->
                            chunks.document("_backup_status")
                                .set(mapOf(
                                    "kind" to "backup_status",
                                    "updatedAt" to FieldValue.serverTimestamp()
                                ))
                                .addOnSuccessListener {
                                    busy.set(false)
                                    onStatus(detail)
                                }
                                .addOnFailureListener { error ->
                                    busy.set(false)
                                    onStatus(
                                        "지도 기록 저장은 완료됐지만 백업 시각 기록에 실패했습니다: " +
                                            (error.localizedMessage ?: error.toString())
                                    )
                                }
                        }

                        if (writes.isEmpty()) {
                            finishSuccessfulBackup(
                                "백업 완료: 전체 지도 기록 " + localCells.size +
                                    "개가 이미 클라우드와 동기화되어 있습니다. 백업 확인 시각을 갱신했습니다."
                            )
                        } else {
                            com.google.android.gms.tasks.Tasks.whenAll(writes)
                                .addOnCompleteListener { task ->
                                    if (task.isSuccessful) {
                                        finishSuccessfulBackup(
                                            "백업 완료: 전체 " + localCells.size +
                                                "개 중 새 기록 " + missingCells.size +
                                                "개를 추가 저장했습니다. 클라우드 기록 " +
                                                cloudCells.size + "개 중 " + restored + "개를 복원했습니다."
                                        )
                                    } else {
                                        busy.set(false)
                                        val error = task.exception
                                        onStatus(
                                            "백업 실패: 클라우드 저장 오류 - " +
                                                (error?.localizedMessage ?: error.toString())
                                        )
                                    }
                                }
                        }
                    } catch (error: Exception)"""
s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit("Could not safely replace incremental backup completion branches")
s = s2

if 'document("_backup_status")' not in s:
    raise SystemExit("Backup status marker write/read missing")
if 'updatedAt' not in s or 'finishSuccessfulBackup' not in s:
    raise SystemExit("Backup timestamp update verification failed")
manager.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 77' not in g or 'versionName = "0.10.24"' not in g:
    raise SystemExit("Expected v0.10.24 before v0.10.25 patch")
g = g.replace('versionCode = 77', 'versionCode = 78', 1)
g = g.replace('versionName = "0.10.24"', 'versionName = "0.10.25"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.25: every successful manual/automatic sync refreshes a dedicated marker.
grep -F 'document("_backup_status")' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
grep -F 'finishSuccessfulBackup' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
grep -F 'versionCode = 78' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.25"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.25 patch applied: successful syncs always refresh a status marker.")
