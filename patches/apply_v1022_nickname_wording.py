from pathlib import Path
import sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"

replacements = {
    "탐험가 닉네임 만들기": "나의 닉네임 만들기",
    "지도와 향후 세계 탐험 랭킹에 표시할 이름입니다.": "MY EARTH에서 나를 표시하는 이름입니다.",
    "Create explorer nickname": "Create my nickname",
    "This name will appear on the map and future global exploration rankings.": "This is the name that represents me in MY EARTH.",
}
counts = {key: 0 for key in replacements}
for path in res.rglob("*.xml"):
    try:
        value = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    updated = value
    for old, new in replacements.items():
        n = updated.count(old)
        if n:
            counts[old] += n
            updated = updated.replace(old, new)
    if updated != value:
        path.write_text(updated, encoding="utf-8")

if counts["탐험가 닉네임 만들기"] < 1 or counts["지도와 향후 세계 탐험 랭킹에 표시할 이름입니다."] < 1:
    raise SystemExit("Could not find both outdated Korean nickname strings in Android resources: " + repr(counts))

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
grep -R -F '나의 닉네임 만들기' app/src/main/res >/dev/null
grep -R -F 'MY EARTH에서 나를 표시하는 이름입니다.' app/src/main/res >/dev/null
! grep -R -F '세계 탐험 랭킹' app/src/main/res
grep -F 'versionCode = 75' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.22"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.22 nickname wording updated in all matching Android resources: " + repr(counts))
