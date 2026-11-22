from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

old_title = '.setTitle(if (required) "탐험가 닉네임 만들기" else "닉네임 변경")'
new_title = '.setTitle(if (required) "나의 닉네임 만들기" else "닉네임 변경")'
old_message = '.setMessage("지도와 향후 세계 탐험 랭킹에 표시할 이름입니다. 닉네임은 2~12자로 입력해 주세요.")'
new_message = '.setMessage("MY EARTH에서 나를 표시하는 이름입니다. 닉네임은 2~12자로 입력해 주세요.")'

if s.count(old_title) != 1:
    raise SystemExit("Expected nickname dialog title was not found exactly once")
if s.count(old_message) != 1:
    raise SystemExit("Expected outdated ranking explanation was not found exactly once")

s = s.replace(old_title, new_title, 1).replace(old_message, new_message, 1)
activity.write_text(s, encoding="utf-8")

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
# v0.10.22: personal nickname wording, with no ranking language.
grep -F '나의 닉네임 만들기' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'MY EARTH에서 나를 표시하는 이름입니다.' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
! grep -F '세계 탐험 랭킹' app/src/main/java/com/earthunlock/app/MainActivity.kt
grep -F 'versionCode = 75' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.22"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.22 nickname wording updated.")
