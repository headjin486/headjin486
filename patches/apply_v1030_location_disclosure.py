from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

old = '"이 앱은 앱이 닫혀 있거나 사용 중이 아닐 때에도 자동 탐험, 현재 위치 표시, " +'
new = '"MY EARTH는 사용자가 자동 탐험을 직접 시작한 경우에만 위치 데이터를 처리합니다. " +'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("Expected location disclosure sentence not found; refusing unsafe rewrite")

for phrase in [
    "사용자가 탐험을 중지할 때까지 Android 포그라운드 서비스로 위치 기록이 계속됩니다.",
    "동의하지 않으면 위치 권한을 요청하거나 자동 탐험을 시작하지 않습니다."
]:
    if phrase not in s:
        raise SystemExit("Expected foreground-service disclosure missing: " + phrase)
if "앱이 닫혀 있거나 사용 중이 아닐 때에도" in s:
    raise SystemExit("Misleading broad location disclosure remains")
activity.write_text(s, encoding="utf-8")

policy = root / "app/src/main/java/com/earthunlock/app/PrivacyPolicyActivity.kt"
p = policy.read_text(encoding="utf-8")
if "사용자가 앱에서 직접 시작합니다" not in p or "포그라운드 서비스" not in p:
    raise SystemExit("In-app privacy policy does not describe the user-started foreground service")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
v = v.replace("versionCode = 82", "versionCode = 83")
v = v.replace('versionName = "0.10.29"', 'versionName = "0.10.30"')
anchor = 'assert "ACCESS_BACKGROUND_LOCATION" not in manifest'
extra = '''
assert "MY EARTH는 사용자가 자동 탐험을 직접 시작한 경우에만 위치 데이터를 처리합니다." in activity
assert "사용자가 탐험을 중지할 때까지 Android 포그라운드 서비스로 위치 기록이 계속됩니다." in activity
assert "앱이 닫혀 있거나 사용 중이 아닐 때에도" not in activity
'''
if extra.strip() not in v:
    if anchor not in v:
        raise SystemExit("Release verifier manifest assertion anchor missing")
    v = v.replace(anchor, anchor + "\n" + extra, 1)
verifier.write_text(v, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 82' not in g or 'versionName = "0.10.29"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.29 / code 82")
g = g.replace('versionCode = 82', 'versionCode = 83', 1)
g = g.replace('versionName = "0.10.29"', 'versionName = "0.10.30"', 1)
gradle.write_text(g, encoding="utf-8")
print("MY EARTH v0.10.30: corrected user-started foreground location disclosure.")
