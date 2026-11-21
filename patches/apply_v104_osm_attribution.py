from pathlib import Path
import re, shutil, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"
files = list((root / "app/src/main/java").rglob("MainActivity.kt"))
if len(files) != 1:
    raise SystemExit(f"Expected one MainActivity.kt, found {len(files)}")
p = files[0]
s = p.read_text(encoding="utf-8")

# Match the attribution view and its parent insertion independent of prior formatting changes.
pattern = r'(?P<indent>^[ \t]*)val attribution = TextView\(this\)\.apply \{[\s\S]*?^[ \t]*\}\n[ \t]*root\.addView\(attribution\)'
replacement = '''\g<indent>val attribution = TextView(this).apply {
            text = "© OpenStreetMap contributors · ODbL"
            textSize = 10f
            setTextColor(Color.rgb(235, 241, 246))
            setPadding(10, 6, 10, 6)
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(Color.argb(185, 7, 23, 45))
                cornerRadius = 12f
            }
            contentDescription = "OpenStreetMap 저작자 표시 및 라이선스 안내 열기"
            setOnClickListener {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.openstreetmap.org/copyright")))
            }
        }
        mapFrame.addView(attribution, FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.END).apply {
            bottomMargin = 10
            marginEnd = 10
        })'''
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.M)
if n != 1:
    lines = [f"{i+1}: {line}" for i,line in enumerate(s.splitlines()) if "attribution" in line.lower() or "OpenStreetMap" in line]
    raise SystemExit("Could not safely locate attribution insertion: " + " | ".join(lines))
p.write_text(s2, encoding="utf-8")

icon_source = root.parent / "assets/my-earth-user-icon.jpg"
if not icon_source.is_file():
    raise SystemExit(f"User icon asset missing: {icon_source}")
drawable = res / "drawable-nodpi"
drawable.mkdir(parents=True, exist_ok=True)
shutil.copyfile(icon_source, drawable / "my_earth_user_icon.jpg")

adaptive = res / "mipmap-anydpi-v26/ic_launcher.xml"
adaptive.parent.mkdir(parents=True, exist_ok=True)
adaptive.write_text('''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/launcher_background" />
    <foreground android:drawable="@drawable/my_earth_user_icon" />
</adaptive-icon>
''', encoding="utf-8")

colors = res / "values/colors.xml"
c = colors.read_text(encoding="utf-8")
c, ncolor = re.subn(r'(<color name="launcher_background">).*?(</color>)', lambda m: m.group(1) + '#FFFFFF' + m.group(2), c, count=1)
if ncolor != 1:
    raise SystemExit("Launcher background color resource missing")
colors.write_text(c, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 57' not in g or 'versionName = "0.10.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 57', 'versionCode = 58', 1)
g = g.replace('versionName = "0.10.3"', 'versionName = "0.10.4"', 1)
gradle.write_text(g, encoding="utf-8")

assert 'mapFrame.addView(attribution' in s2 and 'root.addView(attribution)' not in s2
assert '@drawable/my_earth_user_icon' in adaptive.read_text(encoding="utf-8")
assert (drawable / "my_earth_user_icon.jpg").stat().st_size > 1000
print("v0.10.4 verified: compact OSM overlay and supplied icon image applied")
