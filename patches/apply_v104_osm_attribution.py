from pathlib import Path
import re, shutil, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"
activity_files = list((root / "app/src/main/java").rglob("MainActivity.kt"))
if len(activity_files) != 1:
    raise SystemExit(f"Expected one MainActivity.kt, found {len(activity_files)}")
activity = activity_files[0]
s = activity.read_text(encoding="utf-8")

old = '''        val attribution = TextView(this).apply {
            text = "© OpenStreetMap contributors · ODbL"
            textSize = 11f
            setTextColor(Color.DKGRAY)
            setPadding(8, 3, 8, 3)
            setBackgroundColor(Color.WHITE)
            contentDescription = "OpenStreetMap 저작자 표시 및 라이선스 안내 열기"
            setOnClickListener {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.openstreetmap.org/copyright")))
            }
        }
        root.addView(attribution)'''
new = '''        val attribution = TextView(this).apply {
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
if old not in s:
    raise SystemExit("Exact original OSM attribution block not found; no partial edit made")
s = s.replace(old, new, 1)
activity.write_text(s, encoding="utf-8")

# Apply the exact user-supplied icon image committed beside this patch.
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
c = re.sub(r'(<color name="launcher_background">).*?(</color>)', r'\\g<1>#FFFFFF\\g<2>', c, count=1)
colors.write_text(c, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 57' not in g or 'versionName = "0.10.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 57', 'versionCode = 58', 1)
g = g.replace('versionName = "0.10.3"', 'versionName = "0.10.4"', 1)
gradle.write_text(g, encoding="utf-8")

# Fail the build if either requested change is absent from the generated source.
assert 'mapFrame.addView(attribution' in s and 'root.addView(attribution)' not in s
assert '© OpenStreetMap contributors · ODbL' in s
assert (drawable / "my_earth_user_icon.jpg").is_file()
assert '@drawable/my_earth_user_icon' in adaptive.read_text(encoding="utf-8")
print("v0.10.4 verified: compact OSM overlay and exact user-provided launcher artwork applied")
