from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
# The working internal-test release used these certificates. Reject stale
# Firebase configs rather than ship a regression, especially on Android 17.
config = json.loads((root / "app/google-services.json").read_text(encoding="utf-8"))
if config["project_info"]["project_id"] != "my-earth-a73cb":
    raise SystemExit("Unexpected Firebase project")
clients = [c for c in config["client"] if c["client_info"]["android_client_info"]["package_name"] == "com.earthunlock.app"]
if len(clients) != 1:
    raise SystemExit("Expected one matching Firebase Android app")
oauth = clients[0]["oauth_client"]
if [c["client_id"] for c in oauth if c["client_type"] == 3] != ["760351431659-7k9o7mfmpl316ptnlmlkqra85um20mv2.apps.googleusercontent.com"]:
    raise SystemExit("Unexpected Web OAuth client ID")
certs = {c["android_info"]["certificate_hash"].replace(":", "").lower()
    for c in oauth if c["client_type"] == 1 and c["android_info"]["package_name"] == "com.earthunlock.app"}
required = {
    "3fae4b83e9ced725065e0b07d0d4557fa81e73a0", # local/upload signing
    "30a58f9b14120cf6bc35e308f00ac4020a2cbc5e", # Play legacy
    "7dcc494a9c271ff2072a0796f3cba71ed1506661", # Play signing history
    "cce9721457bd0409ded9b1d7e75e79c4eebdd125", # actual Android 17 signer
}
missing = required - certs
if missing:
    raise SystemExit("Stale Firebase config: missing Android OAuth certificate SHA-1(s): " + ", ".join(sorted(missing)))
print("Firebase release guard passed: expected project, package, Web OAuth client and all observed signing certificates.")

activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")
old = '''            .setTitle("Google 로그인 진단")
            .setMessage(report)
            .setNeutralButton("진단 정보 복사")'''
new = '''            .setTitle("Google 로그인 실패")
            .setMessage("Google 계정 연결을 완료하지 못했습니다.\\n다시 시도해 주세요. 문제가 지속되면 진단 정보를 복사하여 문의해 주세요. 기존 탐험 기록은 변경되지 않습니다. (오류 코드 10)")
            .setNeutralButton("진단 정보 복사")'''
if s.count(old) != 1:
    raise SystemExit("Unexpected diagnostic dialog")
activity.write_text(s.replace(old, new, 1), encoding="utf-8")

for path in [root / "app/build.gradle.kts", root / "scripts/verify-play-release-policy.py"]:
    g = path.read_text(encoding="utf-8")
    if g.count('versionCode = 97') != 1 or g.count('versionName = "0.10.44"') != 1:
        raise SystemExit(f"Unexpected version markers in {path}")
    path.write_text(g.replace('versionCode = 97', 'versionCode = 98').replace('versionName = "0.10.44"', 'versionName = "0.10.45"'), encoding="utf-8")
print("MY EARTH v0.10.45: release-ready error UI and Firebase configuration safeguard. No login logic or user data changes.")
