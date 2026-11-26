from pathlib import Path
import sys
import json

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

anchor = "    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {"
if s.count(anchor) != 1:
    raise SystemExit("Missing unique Google recovery entry point")
# Read only public certificate and OAuth metadata, never accounts, tokens, API keys or locations.
diagnostics = r'''
    @Suppress("DEPRECATION")
    private fun googleSignInDiagnostics(detail: String): String {
        fun fingerprint(bytes: ByteArray): String =
            java.security.MessageDigest.getInstance("SHA-1").digest(bytes)
                .joinToString(":") { String.format(Locale.US, "%02X", it.toInt() and 0xff) }

        val signing = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val info = packageManager.getPackageInfo(
                    packageName, PackageManager.GET_SIGNING_CERTIFICATES
                ).signingInfo
                val current = info?.apkContentsSigners?.map { fingerprint(it.toByteArray()) }
                    ?.joinToString("\n") ?: "확인 불가"
                val history = if (info != null && !info.hasMultipleSigners()) {
                    info.signingCertificateHistory?.map { fingerprint(it.toByteArray()) }
                        ?.joinToString("\n") ?: "없음"
                } else "해당 없음"
                "현재 앱 서명 SHA-1:\n$current\n서명 이력 SHA-1:\n$history"
            } else {
                val current = packageManager.getPackageInfo(
                    packageName, PackageManager.GET_SIGNATURES
                ).signatures?.map { fingerprint(it.toByteArray()) }?.joinToString("\n")
                    ?: "확인 불가"
                "현재 앱 서명 SHA-1:\n$current"
            }
        } catch (_: Exception) {
            "앱 서명 확인 불가"
        }
        val resourceId = resources.getIdentifier("default_web_client_id", "string", packageName)
        val webClient = if (resourceId != 0) getString(resourceId) else "없음"
        val project = runCatching {
            com.google.firebase.FirebaseApp.getInstance().options.projectId
        }.getOrNull() ?: "확인 불가"
        val installer = runCatching {
            packageManager.getInstallerPackageName(packageName)
        }.getOrNull() ?: "확인 불가"
        val version = runCatching {
            packageManager.getPackageInfo(packageName, 0).versionName
        }.getOrNull() ?: "확인 불가"
        return listOf(
            detail, "앱 버전: $version", "Android API: ${Build.VERSION.SDK_INT}",
            "패키지: $packageName", "설치 출처: $installer", signing,
            "Firebase 프로젝트: $project", "Web OAuth ID:\n$webClient"
        ).joinToString("\n\n")
    }

    private fun showGoogleSignInDiagnostics(detail: String) {
        val report = googleSignInDiagnostics(detail)
        AlertDialog.Builder(this)
            .setTitle("Google 로그인 진단")
            .setMessage(report)
            .setNeutralButton("진단 정보 복사") { _, _ ->
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE)
                    as android.content.ClipboardManager
                clipboard.setPrimaryClip(android.content.ClipData.newPlainText("MY EARTH 로그인 진단", report))
                Toast.makeText(this, "진단 정보를 복사했습니다.", Toast.LENGTH_SHORT).show()
            }
            .setPositiveButton("닫기", null)
            .show()
    }

'''
s = s.replace(anchor, diagnostics + anchor, 1)
old = '            Toast.makeText(this, "Google 로그인 실패: $detail", Toast.LENGTH_LONG).show()'
new = '''            if (detail.contains("statusCode=10,")) {
                showGoogleSignInDiagnostics("statusCode=10, DEVELOPER_ERROR")
            } else {
                Toast.makeText(this, "Google 로그인 실패: $detail", Toast.LENGTH_LONG).show()
            }'''
if s.count(old) != 1:
    raise SystemExit("Expected diagnostic toast not found")
s = s.replace(old, new, 1)
old = '            Toast.makeText(this, "Google 로그인 오류: ${error.statusCode}", Toast.LENGTH_LONG).show()'
new = '''            if (error.statusCode == 10) {
                showGoogleSignInDiagnostics("statusCode=10, DEVELOPER_ERROR")
            } else {
                Toast.makeText(this, "Google 로그인 오류: ${error.statusCode}", Toast.LENGTH_LONG).show()
            }'''
if s.count(old) != 1:
    raise SystemExit("Expected ApiException diagnostic toast not found")
s = s.replace(old, new, 1)
activity.write_text(s, encoding="utf-8")

for path in [root / "app/build.gradle.kts", root / "scripts/verify-play-release-policy.py"]:
    g = path.read_text(encoding="utf-8")
    if g.count('versionCode = 96') != 1 or g.count('versionName = "0.10.43"') != 1:
        raise SystemExit(f"Unexpected version markers in {path}")
    path.write_text(g.replace('versionCode = 96', 'versionCode = 97').replace('versionName = "0.10.43"', 'versionName = "0.10.44"'), encoding="utf-8")

# Prevent a build with an unexpected Firebase project, package or web client.
config = json.loads((root / "app/google-services.json").read_text(encoding="utf-8"))
assert config["project_info"]["project_id"] == "my-earth-a73cb"
clients = [c for c in config["client"] if c["client_info"]["android_client_info"]["package_name"] == "com.earthunlock.app"]
assert len(clients) == 1
oauth = clients[0]["oauth_client"]
assert [c["client_id"] for c in oauth if c["client_type"] == 3] == ["760351431659-7k9o7mfmpl316ptnlmlkqra85um20mv2.apps.googleusercontent.com"]
certs = {c["android_info"]["certificate_hash"].replace(":", "").lower()
    for c in oauth if c["client_type"] == 1 and c["android_info"]["package_name"] == "com.earthunlock.app"}
assert {"3fae4b83e9ced725065e0b07d0d4557fa81e73a0","30a58f9b14120cf6bc35e308f00ac4020a2cbc5e"} <= certs
print("MY EARTH v0.10.44: runtime signing certificate & OAuth diagnostics; verified expected Firebase configuration.")
