"""MY EARTH 0.10.47: remove early window-controller initialization from the A dashboard."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")
main = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
old = """        window.statusBarColor = navy
        window.navigationBarColor = navy
        WindowCompat.getInsetsController(window, root).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }
"""
assert s.count(old) == 1
# On newer Android versions the decor/controller may not yet exist during onCreate.
# Colors and icon appearance are purely decorative, so use the existing theme
# instead of calling an insets controller before the view is attached to its window.
s = s.replace(old, "", 1)
assert "WindowCompat.getInsetsController" not in s
assert "setContentView(root)" in s
assert "WindowCompat.setDecorFitsSystemWindows(window, false)" in s
main.write_text(s, encoding="utf-8")

for path in (root / "app/build.gradle.kts", root / "scripts/verify-play-release-policy.py"):
    s = path.read_text(encoding="utf-8")
    assert s.count("versionCode = 99") == 1
    assert s.count('versionName = "0.10.46"') == 1
    path.write_text(s.replace("versionCode = 99", "versionCode = 100").replace('versionName = "0.10.46"', 'versionName = "0.10.47"'), encoding="utf-8")
print("0.10.47 startup fix applied. A dashboard, database, permissions and authentication retained.")
