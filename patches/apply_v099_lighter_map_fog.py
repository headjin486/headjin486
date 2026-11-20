from pathlib import Path
import sys

root = Path(sys.argv[1])
matches = list((root / "app/src/main").rglob("FogOverlay.kt"))
if len(matches) != 1:
    raise SystemExit(f"Expected one FogOverlay.kt, found {len(matches)}")
fog = matches[0]
s = fog.read_text(encoding="utf-8")
old = "Color.argb(232, 10, 20, 36)"
new = "Color.argb(225, 10, 20, 36)"
if old not in s:
    raise SystemExit("Expected v0.9.8 fog color not found; refusing unsafe visual change")
fog.write_text(s.replace(old, new, 1), encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 52' not in g or 'versionName = "0.9.8"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 52', 'versionCode = 53', 1)
g = g.replace('versionName = "0.9.8"', 'versionName = "0.9.9"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.9.9 slightly lighter unexplored map fog.
grep -F 'Color.argb(225, 10, 20, 36)' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'versionCode = 53' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.9.9"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.9 fog opacity patch applied: alpha 232 -> 225")
