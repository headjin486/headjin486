from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# A Google account link is not, by itself, consent to ongoing cloud backup.
# Existing-account restore is a distinct action and gets an explicit consent dialog.
start = a.find("    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {")
end = a.find('    @Deprecated("Google Sign-In activity result bridge")', start)
if start < 0 or end < 0:
    raise SystemExit("Google recovery flow boundaries not found; refusing unsafe edit")

replacement = r'''    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {
        if (restoreExisting) {
            AlertDialog.Builder(this)
                .setTitle("기존 Google 계정 복원 및 백업 설정")
                .setMessage(
                    "기존 Google 계정에 저장된 해금 지도 기록을 현재 휴대폰의 기록과 병합합니다. " +
                        "복원을 진행하면 이후 해금 지도 셀을 클라우드에 자동 백업하도록 함께 켭니다. " +
                        "GPS 원본 좌표와 시간순 이동 경로는 업로드하지 않습니다."
                )
                .setNegativeButton("취소", null)
                .setPositiveButton("동의하고 복원") { _, _ ->
                    launchGoogleRecoverySignIn(restoreExisting = true)
                }
                .show()
        } else {
            // Linking an account protects its identity but does not enable cloud backup.
            launchGoogleRecoverySignIn(restoreExisting = false)
        }
    }

    private fun launchGoogleRecoverySignIn(restoreExisting: Boolean) {
        val webClientId = resources.getIdentifier("default_web_client_id", "string", packageName)
        if (webClientId == 0) {
            Toast.makeText(this, "Firebase 설정에 Google 로그인 정보가 없습니다. Google 로그인 사용 설정 후 google-services.json을 갱신해야 합니다.", Toast.LENGTH_LONG).show()
            return
        }
        val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(getString(webClientId))
            .requestEmail()
            .build()
        val client = GoogleSignIn.getClient(this, options)
        startActivityForResult(client.signInIntent, if (restoreExisting) 9205 else 9204)
    }

'''
a = a[:start] + replacement + a[end:]

# Remove implicit backup activation from every Google-linking branch.
# Preserve a single activation only after the user confirms the existing-account restore dialog.
activity_start = a.find("    override fun onActivityResult(")
if activity_start < 0:
    raise SystemExit("Google activity-result handler not found")
activity_end = a.find("    private fun performAccountDeletion()", activity_start)
if activity_end < 0:
    activity_end = a.find("    private fun requestAndStart()", activity_start)
if activity_end < 0:
    raise SystemExit("Google activity-result handler boundary not found")
handler = a[activity_start:activity_end]
handler = handler.replace("FirebaseBackupManager.setEnabled(this, true)", "")
# Only the existing-account restore branch may turn backup on, after explicit consent.
restore_branch = handler.find("if (requestCode == 9205)")
if restore_branch < 0:
    raise SystemExit("Existing-account restore branch not found")
restore_success = handler.find(".addOnSuccessListener {", restore_branch)
if restore_success < 0:
    raise SystemExit("Restore sign-in success callback not found")
insert_at = handler.find("\n", restore_success) + 1
handler = handler[:insert_at] + "                        FirebaseBackupManager.setEnabled(this, true)\n" + handler[insert_at:]
# Account linking may sync only when backup was already separately enabled.
handler = handler.replace(
    "FirebaseBackupManager.requestSyncIfEnabled(this, store, true)",
    "if (FirebaseBackupManager.isEnabled(this)) {\n                            FirebaseBackupManager.requestSyncIfEnabled(this, store, true)\n                        }"
)
a = a[:activity_start] + handler + a[activity_end:]

# The only automatic enable in this flow must be behind the explicit restore consent.
flow_start = a.find("    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {")
flow_end = a.find("    private fun requestAndStart() {", flow_start)
if flow_start < 0 or flow_end < 0:
    raise SystemExit("Updated Google recovery flow could not be verified")
flow = a[flow_start:flow_end]
handler_start = a.find("    override fun onActivityResult(")
handler_end = a.find("    private fun performAccountDeletion()", handler_start)
if handler_end < 0:
    handler_end = a.find("    private fun requestAndStart()", handler_start)
handler = a[handler_start:handler_end]
restore_pos = handler.find("if (requestCode == 9205)")
enable_pos = handler.find("FirebaseBackupManager.setEnabled(this, true)")
if restore_pos < 0 or enable_pos < restore_pos or handler.count("FirebaseBackupManager.setEnabled(this, true)") != 1:
    raise SystemExit("Expected exactly one backup enable inside the explicit existing-account restore branch")
if '.setPositiveButton("동의하고 복원")' not in flow:
    raise SystemExit("Explicit restore consent action is missing")
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 86' not in g or 'versionName = "0.10.33"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.33 / code 86")
g = g.replace('versionCode = 86', 'versionCode = 87', 1)
g = g.replace('versionName = "0.10.33"', 'versionName = "0.10.34"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if "versionCode = 86" not in v or 'versionName = "0.10.33"' not in v:
    raise SystemExit("Unexpected release verifier version assertions")
v = v.replace("versionCode = 86", "versionCode = 87", 1)
v = v.replace('versionName = "0.10.33"', 'versionName = "0.10.34"', 1)
anchor = 'assert "클라우드 자동 백업은 중지했습니다" in activity'
extra = r'''
flow_start = activity.index("private fun startGoogleRecoveryFlow(restoreExisting: Boolean)")
flow_end = activity.index("private fun requestAndStart()", flow_start)
google_flow = activity[flow_start:flow_end]
assert '.setPositiveButton("동의하고 복원")' in google_flow
assert "기존 Google 계정 복원 및 백업 설정" in google_flow
handler_start = activity.index("override fun onActivityResult(")
handler_end = activity.index("private fun performAccountDeletion()", handler_start)
google_handler = activity[handler_start:handler_end]
assert google_handler.count("FirebaseBackupManager.setEnabled(this, true)") == 1
assert google_handler.index("if (requestCode == 9205)") < google_handler.index("FirebaseBackupManager.setEnabled(this, true)")
assert "클라우드 백업은 별도 동의 후 사용할 수 있습니다." in google_flow
'''
if extra.strip() not in v:
    if anchor not in v:
        raise SystemExit("Release verifier account-deletion assertion anchor not found")
    v = v.replace(anchor, anchor + "\n" + extra, 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.34: Google account linking no longer silently enables cloud backup; existing-account restore now has explicit consent before enabling sync.")
