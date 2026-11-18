from pathlib import Path
import sys

root = Path(sys.argv[1])
strings = root / "app/src/main/res/values-ko/strings.xml"
s = strings.read_text(encoding="utf-8")
replacements = {
    '<string name="header_title">🌍  지구 탐험</string>': '<string name="header_title">🌍  EARTH UNLOCK</string>',
    '<string name="nickname_header">🌍  지구 탐험 · %1$s</string>': '<string name="nickname_header">🌍  EARTH UNLOCK · %1$s</string>',
    '<string name="nickname_header_empty">🌍  지구 탐험 · 닉네임 설정</string>': '<string name="nickname_header_empty">🌍  EARTH UNLOCK · 닉네임 설정</string>',
}
for old, new in replacements.items():
    if old not in s:
        raise SystemExit(f"Brand string not found: {old}")
    s = s.replace(old, new, 1)
strings.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 36' not in g or 'versionName = "0.8.2"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 36', 'versionCode = 37', 1)
g = g.replace('versionName = "0.8.2"', 'versionName = "0.8.3"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 36', 'versionCode = 37')
v = v.replace('versionName = "0.8.2"', 'versionName = "0.8.3"')
v += '''
# Korean UI uses the global EARTH UNLOCK brand consistently.
grep -F '<string name="app_name">EARTH UNLOCK</string>' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F '<string name="header_title">🌍  EARTH UNLOCK</string>' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F '<string name="nickname_header">🌍  EARTH UNLOCK · %1$s</string>' app/src/main/res/values-ko/strings.xml >/dev/null
'''
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.3 Korean brand consistency patch applied")
