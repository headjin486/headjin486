from pathlib import Path
import sys

root = Path(sys.argv[1])
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 94' not in g or 'versionName = "0.10.41"' not in g:
    raise SystemExit("Expected v0.10.41 base version; refusing unsafe version bump")
g = g.replace('versionCode = 94', 'versionCode = 95', 1)
g = g.replace('versionName = "0.10.41"', 'versionName = "0.10.42"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 94' not in v or 'versionName = "0.10.41"' not in v:
    raise SystemExit("Expected v0.10.41 release verifier; refusing unsafe version bump")
v = v.replace('versionCode = 94', 'versionCode = 95', 1)
v = v.replace('versionName = "0.10.41"', 'versionName = "0.10.42"', 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.42 / versionCode 95: refreshed Firebase OAuth configuration.")
