from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
manager = pkg / "FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

if "fun getLastSuccessfulBackup" not in s:
    anchor = "    private fun encode("
    i = s.find(anchor)
    if i < 0:
        raise SystemExit("encode anchor missing")
    methods = r'''
    fun getLastSuccessfulBackup(callback: (String) -> Unit) {
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            callback("아직 연결된 계정이 없습니다.")
            return
        }
        FirebaseFirestore.getInstance().collection("exploration_backups").document(user.uid).get()
            .addOnSuccessListener { doc ->
                val stamp = doc.getTimestamp("lastSuccessfulBackupAt")
                if (stamp == null) callback("아직 완료된 클라우드 백업 기록이 없습니다.")
                else {
                    val formatter = java.text.SimpleDateFormat("yyyy.MM.dd HH:mm", java.util.Locale.getDefault())
                    formatter.timeZone = java.util.TimeZone.getDefault()
                    callback("마지막 정상 백업: " + formatter.format(stamp.toDate()))
                }
            }
            .addOnFailureListener { callback("마지막 백업 시각을 확인하지 못했습니다.") }
    }

    private fun markSuccessfulBackup(uid: String) {
        FirebaseFirestore.getInstance().collection("exploration_backups").document(uid)
            .set(mapOf("lastSuccessfulBackupAt" to FieldValue.serverTimestamp()), SetOptions.merge())
    }

'''
    s = s[:i] + methods + s[i:]

if "import com.google.firebase.firestore.SetOptions" not in s:
    s = s.replace("import com.google.firebase.firestore.FieldValue", "import com.google.firebase.firestore.FieldValue\nimport com.google.firebase.firestore.SetOptions", 1)

if "markSuccessfulBackup(uid)" not in s:
    s = s.replace('''                        if (writes.isEmpty()) {
                            busy.set(false)''', '''                        if (writes.isEmpty()) {
                            markSuccessfulBackup(uid)
                            busy.set(false)''', 1)
    s = s.replace('''                                    if (task.isSuccessful) {
                                        onStatus(''', '''                                    if (task.isSuccessful) {
                                        markSuccessfulBackup(uid)
                                        onStatus(''', 1)
if "markSuccessfulBackup(uid)" not in s:
    raise SystemExit("Could not add successful backup timestamp")
manager.write_text(s, encoding="utf-8")

activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

if "private fun confirmCloudBackupOptIn()" not in a:
    anchor = "    private fun startGoogleRecoveryFlow("
    i = a.find(anchor)
    if i < 0:
        raise SystemExit("Google recovery method missing")
    method = r'''
    private fun confirmCloudBackupOptIn() {
        AlertDialog.Builder(this)
            .setTitle("클라우드 백업도 사용하시겠습니까?")
            .setMessage("Google 계정 연결만으로는 백업이 시작되지 않습니다. 동의하면 해금된 지도 셀 식별자만 클라우드에 저장됩니다. 원본 GPS 좌표와 시간순 이동 경로는 업로드하지 않습니다.")
            .setNegativeButton("계정 연결만 유지", null)
            .setPositiveButton("동의하고 백업 켜기") { _, _ ->
                FirebaseBackupManager.setEnabled(this, true)
                FirebaseBackupManager.requestSyncIfEnabled(this, store, true) { message ->
                    runOnUiThread { Toast.makeText(this, message, Toast.LENGTH_LONG).show() }
                }
            }
            .show()
    }

'''
    a = a[:i] + method + a[i:]

a = a.replace('''                        FirebaseBackupManager.setEnabled(this, true)
                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                        Toast.makeText(this, "Google 계정 연결 완료. 기존 기록을 복원하고 있습니다.", Toast.LENGTH_LONG).show()''',
'''                        Toast.makeText(this, "Google 계정 로그인 완료. 백업 동의 여부를 선택해 주세요.", Toast.LENGTH_LONG).show()
                        confirmCloudBackupOptIn()''', 1)
a = a.replace('''                    FirebaseBackupManager.setEnabled(this, true)
                    FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                    Toast.makeText(this, "이미 Google 계정이 연결되어 있습니다.", Toast.LENGTH_SHORT).show()''',
'''                    Toast.makeText(this, "이미 Google 계정이 연결되어 있습니다.", Toast.LENGTH_SHORT).show()
                    confirmCloudBackupOptIn()''', 1)
a = a.replace('''                            FirebaseBackupManager.setEnabled(this, true)
                            FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                            Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()''',
'''                            Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                            confirmCloudBackupOptIn()''', 1)
a = a.replace('''                                        FirebaseBackupManager.setEnabled(this, true)
                                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                                        Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()''',
'''                                        Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                                        confirmCloudBackupOptIn()''', 1)

# Add an explicit third action for checking account and backup status.
old_items = 'setItems(arrayOf("클라우드 백업 설정 / 지금 백업", "Google 계정 연결 / 기기 변경 복원")) { _, which ->'
new_items = 'setItems(arrayOf("클라우드 백업 설정 / 지금 백업", "Google 계정 연결 / 기기 변경 복원", "계정 및 백업 상태 확인")) { _, which ->'
if old_items not in a:
    raise SystemExit("compact menu items not found")
a = a.replace(old_items, new_items, 1)

old = '''                        } else {
                            AlertDialog.Builder(this@MainActivity)
                                .setTitle("Google 계정으로 기록 보호")'''
new = '''                        } else if (which == 1) {
                            AlertDialog.Builder(this@MainActivity)
                                .setTitle("Google 계정으로 기록 보호")'''
if old not in a:
    raise SystemExit("Google account branch not found")
a = a.replace(old, new, 1)

old = '''                                .setNegativeButton("취소", null)
                                .show()
                        }
                    }
                    .setNegativeButton("닫기", null)'''
new = '''                                .setNegativeButton("취소", null)
                                .show()
                        } else {
                            val user = com.google.firebase.auth.FirebaseAuth.getInstance().currentUser
                            val accountText = when {
                                user == null -> "Google 계정: 연결되지 않음"
                                user.providerData.any { it.providerId == "google.com" } -> "Google 계정: " + (user.email ?: "연결됨")
                                else -> "Google 계정: 기기 익명 계정"
                            }
                            val backupText = if (FirebaseBackupManager.isEnabled(this@MainActivity)) "클라우드 백업: 사용 중" else "클라우드 백업: 꺼짐"
                            FirebaseBackupManager.getLastSuccessfulBackup { last ->
                                runOnUiThread {
                                    AlertDialog.Builder(this@MainActivity)
                                        .setTitle("계정 및 백업 상태")
                                        .setMessage(accountText + "\\n" + backupText + "\\n" + last + "\\n\\n백업 대상: 해금된 지도 셀 식별자\\n백업 제외: 원본 GPS 좌표 및 시간순 이동 경로")
                                        .setPositiveButton("확인", null)
                                        .show()
                                }
                            }
                        }
                    }
                    .setNegativeButton("닫기", null)'''
if old not in a:
    raise SystemExit("Google branch end not found")
a = a.replace(old, new, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 75' not in g or 'versionName = "0.10.22"' not in g:
    raise SystemExit("expected v0.10.22")
g = g.replace('versionCode = 75', 'versionCode = 76', 1)
g = g.replace('versionName = "0.10.22"', 'versionName = "0.10.23"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.23 account and cloud backup status.
grep -F 'confirmCloudBackupOptIn()' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F '계정 및 백업 상태 확인' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'getLastSuccessfulBackup' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
grep -F 'lastSuccessfulBackupAt' app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt >/dev/null
grep -F 'versionCode = 76' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.23"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.23 patch applied.")

# v0.10.24: use the existing chunks collection for backup timestamp reads.
import subprocess
subprocess.run(
    [sys.executable, str(root.parent / "patches/apply_v1024_chunk_backup_timestamp.py"), str(root)],
    check=True,
)
