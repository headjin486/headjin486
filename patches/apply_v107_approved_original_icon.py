from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
repo_icon = Path("app/src/main/res/drawable-nodpi/my_earth_approved_icon.webp")
if not repo_icon.is_file():
    raise SystemExit(f"Approved original artwork missing: {repo_icon}")

res = root / "app/src/main/res"
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
shutil.copyfile(repo_icon, drawable / "my_earth_approved_icon.webp")

adaptive = res / "mipmap-anydpi-v26/ic_launcher.xml"
adaptive.parent.mkdir(parents=True, exist_ok=True)
adaptive.write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/white" />
    <foreground android:drawable="@drawable/my_earth_approved_icon" />
</adaptive-icon>
''', encoding="utf-8")

legacy = res / "mipmap-nodpi"
legacy.mkdir(parents=True, exist_ok=True)
shutil.copyfile(repo_icon, legacy / "ic_launcher.webp")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 60' not in g or 'versionName = "0.10.6"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 60', 'versionCode = 61', 1)
g = g.replace('versionName = "0.10.6"', 'versionName = "0.10.7"', 1)
gradle.write_text(g, encoding="utf-8")

assert (drawable / "my_earth_approved_icon.webp").stat().st_size > 5000
assert "@drawable/my_earth_approved_icon" in adaptive.read_text(encoding="utf-8")
assert (legacy / "ic_launcher.webp").exists()
print("v0.10.7 verified: exact approved MY EARTH artwork installed as adaptive and legacy launcher icon")
