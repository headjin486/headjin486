from pathlib import Path
import sys

root = Path(sys.argv[1])
manager = root / "app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

# The v0.10.16 raw Kotlin template left a single escape before each
# interpolation marker. Remove that escape so Kotlin evaluates the template.
s = s.replace(r"\${", "${")
if r"\${" in s:
    raise SystemExit("Kotlin interpolation escape remains; refusing to continue")
manager.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 70' not in g or 'versionName = "0.10.17"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 70', 'versionCode = 71', 1)
g = g.replace('versionName = "0.10.17"', 'versionName = "0.10.18"', 1)
gradle.write_text(g, encoding="utf-8")
print("Removed remaining Kotlin interpolation escapes and bumped to v0.10.18.")
