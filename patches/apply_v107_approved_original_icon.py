from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
repo_icon = Path("assets/my-earth-approved-icon.png")
if not repo_icon.is_file():
    raise SystemExit("Missing exact user-approved original PNG: assets/my-earth-approved-icon.png")

res = root / "app/src/main/res"
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
shutil.copyfile(repo_icon, drawable / "my_earth_approved_icon.png")

adaptive = res / "mipmap-anydpi-v26/ic_launcher.xml"
adaptive.parent.mkdir(parents=True, exist_ok=True)
adaptive.write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/white" />
    <foreground android:drawable="@drawable/my_earth_approved_icon" />
</adaptive-icon>
''', encoding="utf-8")

legacy = res / "mipmap-nodpi"
legacy.mkdir(parents=True, exist_ok=True)
# Keep the source PNG resource and remove the conflicting WEBP resource.
(legacy / "ic_launcher.webp").unlink(missing_ok=True)
shutil.copyfile(repo_icon, legacy / "ic_launcher.png")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 60' not in g or 'versionName = "0.10.6"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 60', 'versionCode = 61', 1)
g = g.replace('versionName = "0.10.6"', 'versionName = "0.10.8"', 1)
gradle.write_text(g, encoding="utf-8")

assert (drawable / "my_earth_approved_icon.png").read_bytes() == repo_icon.read_bytes()
assert "@drawable/my_earth_approved_icon" in adaptive.read_text(encoding="utf-8")
assert (legacy / "ic_launcher.png").read_bytes() == repo_icon.read_bytes()
assert not (legacy / "ic_launcher.webp").exists()
print("v0.10.8 exact approved PNG applied byte-for-byte to adaptive and legacy launcher resources")
