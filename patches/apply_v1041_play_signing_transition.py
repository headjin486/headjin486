from pathlib import Path
import sys

root = Path(sys.argv[1])
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 93' not in g or 'versionName = "0.10.40"' not in g:
    raise SystemExit("Expected v0.10.40 base version; refusing unsafe version bump")
g = g.replace('versionCode = 93', 'versionCode = 94', 1)
g = g.replace('versionName = "0.10.40"', 'versionName = "0.10.41"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 93' not in v or 'versionName = "0.10.40"' not in v:
    raise SystemExit("Expected v0.10.40 release verifier; refusing unsafe version bump")
v = v.replace('versionCode = 93', 'versionCode = 94', 1)
v = v.replace('versionName = "0.10.40"', 'versionName = "0.10.41"', 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.41 / versionCode 94: Play signing transition build.")
