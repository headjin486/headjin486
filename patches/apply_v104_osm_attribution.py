from pathlib import Path
import sys

root = Path(sys.argv[1])
matches = list((root / "app/src/main/java").rglob("MainActivity.kt"))
if len(matches) != 1:
    raise SystemExit(f"Expected one MainActivity.kt, found {len(matches)}")
p = matches[0]
s = p.read_text(encoding="utf-8")

old = """        val attribution = TextView(this).apply {
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
        root.addView(attribution)"""
new = """        val attribution = TextView(this).apply {
            text = "© OpenStreetMap contributors · ODbL"
            textSize = 9f
            letterSpacing = 0.01f
            setTextColor(Color.rgb(220, 230, 237))
            setPadding(dp(8), dp(4), dp(8), dp(4))
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(Color.argb(165, 7, 27, 50))
                cornerRadius = dp(6).toFloat()
            }
            contentDescription = "OpenStreetMap 저작자 표시 및 라이선스 안내 열기"
            setOnClickListener {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://www.openstreetmap.org/copyright")))
            }
        }
        mapFrame.addView(attribution, FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.END).apply {
            bottomMargin = dp(8)
            marginEnd = dp(8)
        })"""
if old not in s:
    raise SystemExit("Expected OSM attribution block not found; refusing unsafe layout edit")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 57' not in g or 'versionName = "0.10.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 57', 'versionCode = 58', 1)
g = g.replace('versionName = "0.10.3"', 'versionName = "0.10.4"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.4 keeps OSM attribution readable while removing the full-width white strip.
grep -F '© OpenStreetMap contributors · ODbL' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'Color.argb(165, 7, 27, 50)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'Gravity.BOTTOM or Gravity.END' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'versionCode = 58' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.4"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.4: compact dark translucent OSM attribution overlay applied")
