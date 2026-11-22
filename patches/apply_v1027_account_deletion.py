from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# Add the deletion action to the compact account menu introduced in v0.10.21.
if "계정 및 클라우드 데이터 삭제" not in a:
    button_anchor = a.find("val accountBackupButton = Button(this).apply")
    menu_start = a.find("setItems(arrayOf(", button_anchor)
    menu_end = a.find(")) { _, which ->", menu_start)
    if button_anchor < 0 or menu_start < 0 or menu_end < 0:
        raise SystemExit("Compact account menu lambda not found")
    a = a[:menu_end] + ', "계정 및 클라우드 데이터 삭제"' + a[menu_end:]

    google_title = a.find('.setTitle("Google 계정으로 기록 보호")', menu_start)
    branch_start = a.rfind("} else {", menu_start, google_title)
    if google_title < 0 or branch_start < 0:
        raise SystemExit("Google account menu branch anchor not found")
    a = a[:branch_start] + a[branch_start:].replace("} else {", "} else if (which == 1) {", 1)

    # Convert the existing Google-account branch into the middle branch of the
    # if/else-if/else chain. The final else must be inside setItems' lambda.
    menu_close = '\n                        }\n                    }\n                    .setNegativeButton("닫기", null)'
    close_at = a.find(menu_close, google_title)
    if close_at < 0:
        raise SystemExit("Google account branch ending not found")
    replacement = (
        '\n                        }\n'
        '                        if (which == 3) {\n'
        '                            confirmAccountDeletion()\n'
        '                        }\n'
        '                    }'
    )
    a = a[:close_at] + replacement + a[close_at + len(menu_close):]

# Extend the existing Google sign-in result bridge for secure reauthentication before deletion.
a = a.replace(
    "if (requestCode != 9204 && requestCode != 9205) return",
    "if (requestCode != 9204 && requestCode != 9205 && requestCode != 9206) return",
    1
)
a = a.replace(
    "            val credential = GoogleAuthProvider.getCredential(token, null)\n            val auth = FirebaseAuth.getInstance()\n\n            if (requestCode == 9205) {",
    """            val credential = GoogleAuthProvider.getCredential(token, null)
            val auth = FirebaseAuth.getInstance()

            if (requestCode == 9206) {
                val current = auth.currentUser
                if (current == null) {
                    Toast.makeText(this, "로그인 세션이 만료되었습니다. 다시 로그인해 주세요.", Toast.LENGTH_LONG).show()
                    return
                }
                current.reauthenticate(credential)
                    .addOnSuccessListener { performAccountDeletion() }
                    .addOnFailureListener { error ->
                        Toast.makeText(this, "계정 재인증 실패: ${error.localizedMessage}", Toast.LENGTH_LONG).show()
                    }
                return
            }

            if (requestCode == 9205) {""",
    1
)

# Add deletion methods before the location permission flow.
anchor = "    private fun requestAndStart() {"
if "private fun confirmAccountDeletion()" not in a:
    if anchor not in a:
        raise SystemExit("MainActivity requestAndStart insertion point missing")
    methods = r'''
    private fun confirmAccountDeletion() {
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            Toast.makeText(this, "삭제할 MY EARTH 계정이 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }
        AlertDialog.Builder(this)
            .setTitle("계정과 클라우드 데이터를 삭제할까요?")
            .setMessage(
                "Firebase 로그인 계정과 이 계정에 저장된 모든 MY EARTH 클라우드 백업을 영구 삭제합니다. " +
                    "삭제한 계정과 클라우드 백업은 복구할 수 없습니다. " +
                    "휴대폰 내부의 GPS 이동 기록과 지도 데이터는 삭제하지 않고 그대로 둡니다."
            )
            .setNegativeButton("취소", null)
            .setPositiveButton("영구 삭제") { _, _ ->
                val requiresGoogleReauth = user.providerData.any { it.providerId == "google.com" }
                if (requiresGoogleReauth) {
                    val webClientId = resources.getIdentifier("default_web_client_id", "string", packageName)
                    if (webClientId == 0) {
                        Toast.makeText(this, "Google 재인증 설정을 확인할 수 없습니다. 문의 이메일로 삭제를 요청해 주세요.", Toast.LENGTH_LONG).show()
                        return@setPositiveButton
                    }
                    val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                        .requestIdToken(getString(webClientId))
                        .requestEmail()
                        .build()
                    startActivityForResult(
                        GoogleSignIn.getClient(this, options).signInIntent,
                        9206
                    )
                } else {
                    performAccountDeletion()
                }
            }
            .show()
    }

    private fun performAccountDeletion() {
        FirebaseBackupManager.deleteAccountAndCloudData { success, message ->
            runOnUiThread {
                if (success) {
                    FirebaseBackupManager.setEnabled(this, false)
                    FirebaseAuth.getInstance().signOut()
                    Toast.makeText(
                        this,
                        "Firebase 계정과 클라우드 백업을 삭제했습니다. 기기 내부 GPS 기록은 유지됩니다.",
                        Toast.LENGTH_LONG
                    ).show()
                } else {
                    Toast.makeText(
                        this,
                        "계정 삭제를 완료하지 못했습니다: ${message ?: "잠시 후 다시 시도하거나 문의 이메일로 요청해 주세요."}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

'''
    a = a.replace(anchor, methods + anchor, 1)
activity.write_text(a, encoding="utf-8")

manager = pkg / "FirebaseBackupManager.kt"
m = manager.read_text(encoding="utf-8")
if "fun deleteAccountAndCloudData" not in m:
    anchor = "    private fun encode(cells: List<Pair<Long, Long>>): String {"
    if anchor not in m:
        raise SystemExit("FirebaseBackupManager encode insertion point missing")
    method = r'''
    /** Delete all Firestore backup chunks first, then permanently delete the signed-in Firebase account. */
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
                                    onComplete(false, error.localizedMessage ?: "Firebase 계정 삭제 실패")
                                }
                        }
                        .addOnFailureListener { error ->
                            onComplete(false, error.localizedMessage ?: "클라우드 백업 삭제 실패")
                        }
                } catch (error: Exception) {
                    onComplete(false, error.localizedMessage ?: "클라우드 백업 삭제 처리 실패")
                }
            }
            .addOnFailureListener { error ->
                onComplete(false, error.localizedMessage ?: "클라우드 백업 조회 실패")
            }
    }

'''
    m = m.replace(anchor, method + anchor, 1)
manager.write_text(m, encoding="utf-8")

# Add source-level checks for the in-app deletion route and Firestore deletion-before-Auth order.
verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += '''
# v0.10.27 account deletion must remove all account backup chunks before deleting Firebase Auth.
python - <<'PY'
from pathlib import Path
a = Path("app/src/main/java/com/earthunlock/app/MainActivity.kt").read_text(encoding="utf-8")
m = Path("app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt").read_text(encoding="utf-8")
assert "계정 및 클라우드 데이터 삭제" in a
assert "private fun confirmAccountDeletion()" in a
assert "private fun performAccountDeletion()" in a
assert "fun deleteAccountAndCloudData" in m
assert m.index("Tasks.whenAll(batches)") < m.index("user.delete()")
assert "exploration_backups" in m and "collection(\\"chunks\\")" in m
PY
'''
verify.write_text(v, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 79' not in g or 'versionName = "0.10.26"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.26")
g = g.replace('versionCode = 79', 'versionCode = 80', 1)
g = g.replace('versionName = "0.10.26"', 'versionName = "0.10.27"', 1)
gradle.write_text(g, encoding="utf-8")
print("MY EARTH v0.10.27 account deletion: remove all Firestore backup chunks, then delete Firebase Auth account; preserve local SQLite exploration records.")
