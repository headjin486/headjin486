from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")
old = "accountBackupButton.postDelayed({"
if old not in a:
    raise SystemExit("Expected deferred account menu dispatch not found")
a = a.replace(old, "panel.postDelayed({", 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 91' not in g or 'versionName = "0.10.38"' not in g:
    raise SystemExit("Expected v0.10.38 / versionCode 91")
g = g.replace('versionCode = 91', 'versionCode = 92', 1)
g = g.replace('versionName = "0.10.38"', 'versionName = "0.10.39"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 91' not in v or 'versionName = "0.10.38"' not in v:
    raise SystemExit("Expected v0.10.38 verifier assertions")
v = v.replace('versionCode = 91', 'versionCode = 92', 1)
v = v.replace('versionName = "0.10.38"', 'versionName = "0.10.39"', 1)
v = v.replace('assert "accountBackupButton.postDelayed({" in menu', 'assert "panel.postDelayed({" in menu')
verifier.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.39: use the enclosing panel as the deferred dispatcher to avoid self-reference during local view initialization.")
