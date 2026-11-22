from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

start = a.find("    private fun performAccountDeletion() {")
end = a.find("    private fun requestAndStart()", start)
if start < 0 or end < 0:
    raise SystemExit("Account deletion handler boundaries not found; refusing unsafe edit")

replacement = r'''    private fun performAccountDeletion() {
        FirebaseBackupManager.deleteAccountAndCloudData { success, message ->
            runOnUiThread {
                if (success) {
                    FirebaseBackupManager.setEnabled(this@MainActivity, false)
                    FirebaseAuth.getInstance().signOut()
                    Toast.makeText(
                        this@MainActivity,
                        "Firebase 계정과 클라우드 백업을 삭제했습니다. 기기 내부 GPS 기록은 유지됩니다.",
                        Toast.LENGTH_LONG
                    ).show()
                } else {
                    // Stop automatic sync after any deletion failure so deleted backup chunks
                    // cannot be silently recreated while the account-removal request is pending.
                    FirebaseBackupManager.setEnabled(this@MainActivity, false)
                    Toast.makeText(
                        this@MainActivity,
                        "계정 삭제를 완료하지 못했습니다. 클라우드 자동 백업은 중지했습니다: ${message ?: "문의 이메일로 삭제를 요청해 주세요."}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

'''
a = a[:start] + replacement + a[end:]
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 85' not in g or 'versionName = "0.10.32"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.32 / code 85")
g = g.replace('versionCode = 85', 'versionCode = 86', 1)
g = g.replace('versionName = "0.10.32"', 'versionName = "0.10.33"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 85' not in v or 'versionName = "0.10.32"' not in v:
    raise SystemExit("Unexpected release verifier version assertions")
v = v.replace("versionCode = 85", "versionCode = 86", 1)
v = v.replace('versionName = "0.10.32"', 'versionName = "0.10.33"', 1)
anchor = 'assert "headjin486@gmail.com" in manager'
if anchor not in v:
    raise SystemExit("Account deletion support-email assertion not found")
v = v.replace(anchor, anchor + '''
assert "FirebaseBackupManager.setEnabled(this@MainActivity, false)" in activity
assert "클라우드 자동 백업은 중지했습니다" in activity
# Explicit cloud-backup consent must remain separate from Google account linking.
consent_start = activity.index("private fun confirmCloudBackupOptIn()")
consent_end = activity.index("private fun startGoogleRecoveryFlow(", consent_start)
consent = activity[consent_start:consent_end]
assert '.setPositiveButton("동의하고 백업 켜기")' in consent
assert consent.count("FirebaseBackupManager.setEnabled(this, true)") == 1
google_start = activity.index("override fun onActivityResult(")
google_end = activity.index("private fun confirmAccountDeletion()", google_start)
google_flow = activity[google_start:google_end]
assert "FirebaseBackupManager.setEnabled(this, true)" not in google_flow
assert google_flow.count("confirmCloudBackupOptIn()") >= 3
''', 1)
verifier.write_text(v, encoding="utf-8")
print("v0.10.33 replaces the account deletion handler and disables automatic cloud backup after any deletion failure.")
