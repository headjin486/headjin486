from pathlib import Path
import re, sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
text = activity.read_text(encoding="utf-8")

# Clarify the denominator beside the existing percentage; preserve the calculation.
pattern = r'countText\.text\s*=\s*"([^"\n]*\\n)\$percentLabel(\\n[^"]*)"'
updated, count = re.subn(
    pattern,
    lambda m: 'countText.text = "' + m.group(1) + '$percentLabel (지구 전체 지도 대비)' + m.group(2) + '"',
    text,
    count=1
)
if count != 1:
    raise SystemExit("Main map percentage display anchor missing or ambiguous")
activity.write_text(updated, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 56' not in g or 'versionName = "0.10.2"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 56', 'versionCode = 57', 1)
g = g.replace('versionName = "0.10.2"', 'versionName = "0.10.3"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.3 clarify that the map percentage is measured against the whole Earth map.
grep -F '지구 전체 지도 대비' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'versionCode = 57' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.3"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.3 clarified map percentage denominator; calculation and user data unchanged")
