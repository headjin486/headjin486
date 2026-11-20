from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
fog = pkg / "FogOverlay.kt"
s = fog.read_text(encoding="utf-8")

old = "private val fogColor = Color.argb(244, 5, 13, 29)"
new = "private val fogColor = Color.argb(232, 10, 20, 36)"
if old not in s:
    raise SystemExit("Expected v0.9.7 fog color not found; refusing unsafe visual change")
s = s.replace(old, new, 1)
fog.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 51' not in g or 'versionName = "0.9.7"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 51', 'versionCode = 52', 1)
g = g.replace('versionName = "0.9.7"', 'versionName = "0.9.8"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.9.8 slightly lighter fog, retaining a dark unexplored-map treatment.
grep -F 'Color.argb(232, 10, 20, 36)' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'versionCode = 52' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.9.8"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.8 lighter map fog patch applied")
