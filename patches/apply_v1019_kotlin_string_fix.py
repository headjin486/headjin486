from pathlib import Path
import sys

root = Path(sys.argv[1])
manager = root / "app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt"
s = manager.read_text(encoding="utf-8")

s = s.replace('error.localizedMessage ?: "알 수 없는 오류"', 'error.localizedMessage ?: error.javaClass.simpleName')
s = s.replace('error?.localizedMessage ?: "네트워크 또는 Firestore 규칙을 확인하세요."', 'error?.localizedMessage ?: error.toString()')

# The fallback phrases may also appear in unrelated UI text; the exact
# problematic interpolation expressions above are replaced directly.

manager.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 71' not in g or 'versionName = "0.10.18"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 71', 'versionCode = 72', 1)
g = g.replace('versionName = "0.10.18"', 'versionName = "0.10.19"', 1)
gradle.write_text(g, encoding="utf-8")
print("Removed nested Kotlin fallback string literals and bumped to v0.10.19.")
