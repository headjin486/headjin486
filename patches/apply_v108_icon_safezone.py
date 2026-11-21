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

# Android adaptive icons are masked by the launcher. Keep all original artwork,
# including the outer MY EARTH lettering, inside the central 66% safe region.
scale = 0.66
side = round(1024 * scale)
inner = im.resize((side, side), Image.Resampling.LANCZOS)
# The approved artwork uses a dark green full-bleed background. Reuse its
# corner color so the added safety margin blends into the original artwork.
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
adaptive.write_text(f'''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@android:color/black" />
    <foreground android:drawable="@drawable/my_earth_approved_icon_safezone" />
</adaptive-icon>
'''.replace('@android:color/black', '@drawable/my_earth_icon_background'), encoding="utf-8")
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
if 'versionCode = 61' not in g or 'versionName = "0.10.8"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 61', 'versionCode = 62', 1)
g = g.replace('versionName = "0.10.8"', 'versionName = "0.10.9"', 1)
gradle.write_text(g, encoding="utf-8")

assert Image.open(out).size == (1024, 1024)
assert Image.open(legacy / "ic_launcher.png").size == (1024, 1024)
assert "@drawable/my_earth_approved_icon_safezone" in adaptive.read_text(encoding="utf-8")
print("v0.10.9 launcher artwork scaled to 66% adaptive-icon safe zone; original artwork preserved")
