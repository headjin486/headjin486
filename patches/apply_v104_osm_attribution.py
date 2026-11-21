from pathlib import Path
import re, sys

root = Path(sys.argv[1])
files = list((root / "app/src/main/java").rglob("MainActivity.kt"))
if len(files) != 1:
    raise SystemExit(f"Expected one MainActivity.kt, found {len(files)}")
p = files[0]
s = p.read_text(encoding="utf-8")

# Add the OSM attribution overlay without changing or replacing launcher artwork.
pattern = r'(?P<indent>^[ \\t]*)val attribution = TextView\\(this\\)\\.apply \\{[\\s\\S]*?^[ \\t]*\\}\\n[ \\t]*root\\.addView\\(attribution\\)'
replacement = r'''\\g<indent>val attribution = TextView(this).apply {
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
        mapFrame.addView(attribution, FrameLayout.LayoutParams(-2, -2, Gravity.TOP or Gravity.START).apply {
            topMargin = 10
            marginStart = 10
        })'''
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.M)
if n != 1:
    lines = [f"{i+1}: {line}" for i,line in enumerate(s.splitlines()) if "attribution" in line.lower() or "OpenStreetMap" in line]
    raise SystemExit("Could not safely locate attribution insertion: " + " | ".join(lines))
p.write_text(s2, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 57' not in g or 'versionName = "0.10.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 57', 'versionCode = 59', 1)
g = g.replace('versionName = "0.10.3"', 'versionName = "0.10.5"', 1)
gradle.write_text(g, encoding="utf-8")

assert 'mapFrame.addView(attribution' in s2 and 'root.addView(attribution)' not in s2
print("v0.10.5 verified: OSM attribution overlay applied; launcher artwork left untouched")
