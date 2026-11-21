from pathlib import Path
from PIL import Image
import sys

root = Path(sys.argv[1])
source = Path("assets/my-earth-approved-icon.png")
if not source.is_file():
    raise SystemExit("Missing approved source icon")
im = Image.open(source).convert("RGBA")
if im.size != (1024, 1024):
    raise SystemExit(f"Unexpected approved icon dimensions: {im.size}")

# Fine adjustment requested after reviewing v0.10.10: 78% fills the icon
# more completely while preserving the approved artwork and its proportions.
scale = 0.78
side = round(1024 * scale)
inner = im.resize((side, side), Image.Resampling.LANCZOS)
px = [im.getpixel(p) for p in ((0, 0), (1023, 0), (0, 1023), (1023, 1023))]
bg = tuple(round(sum(c[i] for c in px) / len(px)) for i in range(3)) + (255,)
canvas = Image.new("RGBA", (1024, 1024), bg)
canvas.alpha_composite(inner, ((1024 - side) // 2, (1024 - side) // 2))

res = root / "app/src/main/res"
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
out = drawable / "my_earth_approved_icon_safezone.png"
canvas.save(out, format="PNG", optimize=True)

adaptive = res / "mipmap-anydpi-v26/ic_launcher.xml"
adaptive.parent.mkdir(parents=True, exist_ok=True)
adaptive.write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/my_earth_icon_background" />
    <foreground android:drawable="@drawable/my_earth_approved_icon_safezone" />
</adaptive-icon>
''', encoding="utf-8")
bg_xml = res / "drawable/my_earth_icon_background.xml"
bg_xml.parent.mkdir(parents=True, exist_ok=True)
bg_xml.write_text(f'''<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}" />
</shape>
''', encoding="utf-8")

legacy = res / "mipmap-nodpi"
legacy.mkdir(parents=True, exist_ok=True)
(legacy / "ic_launcher.webp").unlink(missing_ok=True)
canvas.save(legacy / "ic_launcher.png", format="PNG", optimize=True)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 63' not in g or 'versionName = "0.10.10"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 63', 'versionCode = 64', 1)
g = g.replace('versionName = "0.10.10"', 'versionName = "0.10.11"', 1)
gradle.write_text(g, encoding="utf-8")

assert Image.open(out).size == (1024, 1024)
assert Image.open(legacy / "ic_launcher.png").size == (1024, 1024)
assert "my_earth_approved_icon_safezone" in adaptive.read_text(encoding="utf-8")
print("v0.10.11 launcher artwork scaled to 78%; original artwork and proportions preserved")
