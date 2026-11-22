from pathlib import Path
import re, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"

def update_string(relative, key, value):
    path = res / relative
    xml = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(<string\\s+name="' + re.escape(key) + r'"[^>]*>).*?(</string>)', re.S)
    updated, count = pattern.subn(lambda m: m.group(1) + value + m.group(2), xml, count=1)
    if count != 1:
        raise SystemExit(f"Expected exactly one {key} in {relative}; found {count}")
    path.write_text(updated, encoding="utf-8")

# Korean UI
update_string("values-ko/strings.xml", "nickname_accessibility", "나의 닉네임 설정")
update_string("values-ko/strings.xml", "nickname_create_title", "나의 닉네임 만들기")
update_string("values-ko/strings.xml", "nickname_message", "MY EARTH에서 나를 표시하는 이름입니다. 닉네임은 2~12자로 입력해 주세요.")

# English UI
update_string("values/strings.xml", "nickname_accessibility", "Set my nickname")
update_string("values/strings.xml", "nickname_create_title", "Create my nickname")
update_string("values/strings.xml", "nickname_message", "This is the name that represents me in MY EARTH. Enter 2–12 characters.")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 74' not in g or 'versionName = "0.10.21"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.21")
g = g.replace('versionCode = 74', 'versionCode = 75', 1)
g = g.replace('versionName = "0.10.21"', 'versionName = "0.10.22"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.22: personal nickname wording, without ranking references.
grep -F '<string name="nickname_create_title">나의 닉네임 만들기</string>' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F 'MY EARTH에서 나를 표시하는 이름입니다.' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F '<string name="nickname_create_title">Create my nickname</string>' app/src/main/res/values/strings.xml >/dev/null
grep -F 'This is the name that represents me in MY EARTH.' app/src/main/res/values/strings.xml >/dev/null
! grep -F '세계 탐험 랭킹' app/src/main/res/values-ko/strings.xml
grep -F 'versionCode = 75' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.22"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.22 Korean/English personal nickname wording applied.")
