from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

# The v0.10.16 raw Python template emitted two backslashes before Kotlin
# interpolation markers. Kotlin needs the interpolation marker directly.
s = s.replace("\\\\${", "${")

# v0.10.16 replaced the sync-method region up to encode(), unintentionally
# removing the cloud-delete method introduced in v0.10.14.
if "fun deleteCloudBackup" not in s:
    anchor = "    private fun encode(cells: List<Pair<Long, Long>>): String {"
    if anchor not in s:
        raise SystemExit("Firebase backup encode insertion point missing")
    method = r'''
    /** Delete only this user's cloud backup documents; local SQLite data is untouched. */
    fun deleteCloudBackup(onComplete: (Boolean) -> Unit) {
        val uid = FirebaseAuth.getInstance().currentUser?.uid
        if (uid.isNullOrBlank()) {
            onComplete(true)
            return
        }
        val chunks = FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(uid).collection("chunks")
        chunks.get()
            .addOnSuccessListener { snapshot ->
                if (snapshot.isEmpty) {
                    onComplete(true)
                } else {
                    val tasks = snapshot.documents.chunked(400).map { documents ->
                        val batch = FirebaseFirestore.getInstance().batch()
                        documents.forEach { batch.delete(it.reference) }
                        batch.commit()
                    }
                    com.google.android.gms.tasks.Tasks.whenAll(tasks)
                        .addOnCompleteListener { onComplete(it.isSuccessful) }
                }
            }
            .addOnFailureListener { onComplete(false) }
    }

'''
    s = s.replace(anchor, method + anchor, 1)

manager.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 69' not in g or 'versionName = "0.10.16"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 69', 'versionCode = 70', 1)
g = g.replace('versionName = "0.10.16"', 'versionName = "0.10.17"', 1)
gradle.write_text(g, encoding="utf-8")
print("Fixed Kotlin interpolation, restored cloud-backup deletion, and bumped to v0.10.17.")
