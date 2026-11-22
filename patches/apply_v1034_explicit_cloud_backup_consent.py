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

old_already = r'''                if (current?.providerData?.any { it.providerId == "google.com" } == true) {
                    FirebaseBackupManager.setEnabled(this, true)
                    FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                    Toast.makeText(this, "Google 계정 연결 완료. 기존 기록을 복원하고 있습니다.", Toast.LENGTH_LONG).show()
                } else if (current != null) {'''
new_already = r'''                if (current?.providerData?.any { it.providerId == "google.com" } == true) {
                    if (FirebaseBackupManager.isEnabled(this)) {
                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                    }
                    Toast.makeText(this, "이미 Google 계정이 연결되어 있습니다. 클라우드 백업은 별도 설정에서 동의한 경우에만 실행됩니다.", Toast.LENGTH_LONG).show()
                } else if (current != null) {'''
if old_already not in a:
    raise SystemExit("Already-linked Google branch not found")
a = a.replace(old_already, new_already, 1)

old_link = r'''                        .addOnSuccessListener {
                            FirebaseBackupManager.setEnabled(this, true)
                            FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                            Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                        }'''
new_link = r'''                        .addOnSuccessListener {
                            if (FirebaseBackupManager.isEnabled(this)) {
                                FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                            }
                            Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다. 클라우드 백업은 별도 동의 후 사용할 수 있습니다.", Toast.LENGTH_LONG).show()
                        }'''
if old_link not in a:
    raise SystemExit("Current anonymous account Google-link success block not found")
a = a.replace(old_link, new_link, 1)

old_anon = r'''                                    .addOnSuccessListener {
                                        FirebaseBackupManager.setEnabled(this, true)
                                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                                        Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                                    }'''
new_anon = r'''                                    .addOnSuccessListener {
                                        if (FirebaseBackupManager.isEnabled(this)) {
                                            FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                                        }
                                        Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다. 클라우드 백업은 별도 동의 후 사용할 수 있습니다.", Toast.LENGTH_LONG).show()
                                    }'''
if old_anon not in a:
    raise SystemExit("New anonymous account Google-link success block not found")
a = a.replace(old_anon, new_anon, 1)

# The only automatic enable in this flow must be behind the explicit restore consent.
flow_start = a.find("    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {")
flow_end = a.find("    private fun requestAndStart() {", flow_start)
if flow_start < 0 or flow_end < 0:
    raise SystemExit("Updated Google recovery flow could not be verified")
flow = a[flow_start:flow_end]
if flow.count("FirebaseBackupManager.setEnabled(this, true)") != 1:
    raise SystemExit("Expected exactly one consent-gated backup enable in Google recovery flow")
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
assert google_flow.count("FirebaseBackupManager.setEnabled(this, true)") == 1
assert "클라우드 백업은 별도 동의 후 사용할 수 있습니다." in google_flow
'''
if extra.strip() not in v:
    if anchor not in v:
        raise SystemExit("Release verifier account-deletion assertion anchor not found")
    v = v.replace(anchor, anchor + "\n" + extra, 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.34: Google account linking no longer silently enables cloud backup; existing-account restore now has explicit consent before enabling sync.")
