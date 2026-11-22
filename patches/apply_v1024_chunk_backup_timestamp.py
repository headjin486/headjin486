from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

start = s.find("    fun getLastSuccessfulBackup(")
end = s.find("    private fun encode(", start)
if start < 0 or end < 0:
    raise SystemExit("v0.10.23 backup timestamp methods not found")

replacement = r"""
    /**
     * Read the timestamp from the existing chunks subcollection.
     * This uses the same Firestore path and read permission as normal backup sync.
     */
    fun getLastSuccessfulBackup(callback: (String) -> Unit) {
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            callback("아직 연결된 계정이 없습니다.")
            return
        }
        FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(user.uid)
            .collection("chunks").get()
            .addOnSuccessListener { snapshot ->
                val stamp = snapshot.documents
                    .mapNotNull { it.getTimestamp("updatedAt") }
                    .maxByOrNull { it.toDate().time }
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
s = s[:start] + replacement + s[end:]
s = s.replace("                            markSuccessfulBackup(uid)\n", "")
s = s.replace("                                        markSuccessfulBackup(uid)\n", "")
s = s.replace("import com.google.firebase.firestore.SetOptions\n", "")
if "lastSuccessfulBackupAt" in s or "markSuccessfulBackup" in s:
    raise SystemExit("Old parent-document timestamp implementation remains")
if '.collection("chunks").get()' not in s or 'getTimestamp("updatedAt")' not in s:
    raise SystemExit("Chunk timestamp lookup verification failed")
manager.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 76' not in g or 'versionName = "0.10.23"' not in g:
    raise SystemExit("Expected v0.10.23 before v0.10.24 patch")
g = g.replace('versionCode = 76', 'versionCode = 77', 1)
g = g.replace('versionName = "0.10.23"', 'versionName = "0.10.24"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.24: backup timestamp is read from the existing chunks collection.
grep -F 'getTimestamp("updatedAt")' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
grep -F '.collection("chunks").get()' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
! grep -F 'lastSuccessfulBackupAt' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt
grep -F 'versionCode = 77' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.24"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.24 patch applied: timestamp reads from existing backup chunks.")

# v0.10.25: refresh a dedicated timestamp marker after every successful sync.
import subprocess
subprocess.run(
    [sys.executable, str(root.parent / "patches/apply_v1025_backup_timestamp_refresh.py"), str(root)],
    check=True,
)
