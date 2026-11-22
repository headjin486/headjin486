from pathlib import Path
import sys

root = Path(sys.argv[1])
manager = root / "app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")
start = s.find("    fun deleteAccountAndCloudData(")
end = s.find("    private fun encode(", start)
if start < 0 or end < 0:
    raise SystemExit("Account deletion method boundaries not found; refusing unsafe edit")

replacement = r'''    /**
     * Delete this UID's cloud backup chunks, then delete the Firebase Auth user.
     * This is intentionally non-atomic: if Auth deletion fails after chunk deletion,
     * the callback explicitly reports the partial-completion state for recovery.
     */
    fun deleteAccountAndCloudData(onComplete: (Boolean, String?) -> Unit) {
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            onComplete(false, "로그인된 계정을 찾을 수 없습니다.")
            return
        }
        val chunks = FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(user.uid).collection("chunks")
        chunks.get()
            .addOnSuccessListener { snapshot ->
                try {
                    val batches = snapshot.documents.chunked(400).map { documents ->
                        val batch = FirebaseFirestore.getInstance().batch()
                        documents.forEach { batch.delete(it.reference) }
                        batch.commit()
                    }
                    com.google.android.gms.tasks.Tasks.whenAll(batches)
                        .addOnSuccessListener {
                            user.delete()
                                .addOnSuccessListener { onComplete(true, null) }
                                .addOnFailureListener { error ->
                                    val detail = error.localizedMessage ?: "원인을 확인할 수 없습니다."
                                    val message = if (error is com.google.firebase.auth.FirebaseAuthRecentLoginRequiredException) {
                                        if (user.isAnonymous) {
                                            "클라우드 백업은 삭제됐지만 익명 계정 삭제에 최근 인증이 필요합니다. 익명 계정은 Google 재인증을 할 수 없으므로 ${supportEmailForDeletion()}로 계정 삭제를 요청해 주세요. 상세: $detail"
                                        } else {
                                            "클라우드 백업은 삭제됐지만 계정 삭제에 최근 인증이 필요합니다. 다시 로그인한 뒤 삭제를 재시도해 주세요. 상세: $detail"
                                        }
                                    } else {
                                        "클라우드 백업은 삭제됐지만 Firebase 계정 삭제가 실패했습니다. 네트워크 연결과 로그인 상태를 확인한 뒤 재시도하거나 ${supportEmailForDeletion()}로 삭제를 요청해 주세요. 상세: $detail"
                                    }
                                    onComplete(false, message)
                                }
                        }
                        .addOnFailureListener { error ->
                            onComplete(false, "클라우드 백업 삭제가 완료되지 않아 계정은 삭제하지 않았습니다. 다시 시도해 주세요. 상세: ${error.localizedMessage ?: "알 수 없는 오류"}")
                        }
                } catch (error: Exception) {
                    onComplete(false, "클라우드 백업 삭제 처리 중 오류가 발생해 계정은 삭제하지 않았습니다. 상세: ${error.localizedMessage ?: "알 수 없는 오류"}")
                }
            }
            .addOnFailureListener { error ->
                onComplete(false, "클라우드 백업을 확인하지 못해 계정은 삭제하지 않았습니다. 네트워크 연결 후 다시 시도해 주세요. 상세: ${error.localizedMessage ?: "알 수 없는 오류"}")
            }
    }

    private fun supportEmailForDeletion(): String = "headjin486@gmail.com"

'''
s = s[:start] + replacement + s[end:]
manager.write_text(s, encoding="utf-8")

activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")
if "클라우드 백업은 삭제됐지만" not in s:
    raise SystemExit("Partial deletion recovery messages were not written")
if "private fun performAccountDeletion()" not in a:
    raise SystemExit("Account deletion UI callback not found")
if "FirebaseBackupManager.deleteAccountAndCloudData" not in a:
    raise SystemExit("Account deletion manager call not found")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 84' not in g or 'versionName = "0.10.31"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.31 / code 84")
g = g.replace('versionCode = 84', 'versionCode = 85', 1)
g = g.replace('versionName = "0.10.31"', 'versionName = "0.10.32"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if "versionCode = 84" not in v or 'versionName = "0.10.31"' not in v:
    raise SystemExit("Unexpected release verifier version assertions")
v = v.replace("versionCode = 84", "versionCode = 85", 1)
v = v.replace('versionName = "0.10.31"', 'versionName = "0.10.32"', 1)
anchor = 'assert manager.index("Tasks.whenAll(batches)") < manager.index("user.delete()")'
if anchor not in v:
    raise SystemExit("Deletion order assertion not found")
v = v.replace(anchor, anchor + '''
assert "FirebaseAuthRecentLoginRequiredException" in manager
assert "클라우드 백업은 삭제됐지만" in manager
assert "클라우드 백업 삭제가 완료되지 않아 계정은 삭제하지 않았습니다" in manager
assert "headjin486@gmail.com" in manager''', 1)
verifier.write_text(v, encoding="utf-8")
print("v0.10.32 account deletion now reports partial completion explicitly and provides recovery instructions.")
