from pathlib import Path
import re, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"
gradle = root / "app/build.gradle.kts"

# MY EARTH launcher icon: a luminous Earth with a continuous mint M-shaped route.
icon = res / "drawable/ic_launcher_foreground.xml"
icon.write_text(r'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#071B32" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#123B63" android:pathData="M54,9a45,45 0,1 0,0 90a45,45 0,1 0,0 -90"/>
    <path android:fillColor="#0B2949" android:pathData="M54,15a39,39 0,1 0,0 78a39,39 0,1 0,0 -78"/>
    <path android:fillColor="#2B7190" android:pathData="M24,38l9,-9 13,-4 8,5 -4,8 -11,2 -4,8 -10,1z M65,27l13,4 8,9 -5,7 -11,-2 -7,-8z M38,58l9,-7 8,4 4,12 -8,12 -8,-4z M67,57l13,-4 8,9 -6,15 -10,7 -7,-9z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#56B8C8" android:strokeWidth="1.2" android:pathData="M54,10a44,44 0,1 0,0 88a44,44 0,1 0,0 -88"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#A7DCCB" android:strokeWidth="5.5" android:strokeLineCap="round" android:strokeLineJoin="round" android:pathData="M18,72 C29,72 31,39 43,39 S53,69 63,59 S76,30 88,30"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#E0FFF3" android:strokeWidth="1.4" android:strokeLineCap="round" android:pathData="M18,72 C29,72 31,39 43,39 S53,69 63,59 S76,30 88,30"/>
    <path android:fillColor="#E8FFF8" android:pathData="M13,72a5,5 0,1 0,10 0a5,5 0,1 0,-10 0"/>
    <path android:fillColor="#A7DCCB" android:pathData="M82,30a6,6 0,1 0,12 0a6,6 0,1 0,-12 0"/>
    <path android:fillColor="#FFFFFF" android:pathData="M85,30a3,3 0,1 0,6 0a3,3 0,1 0,-6 0"/>
</vector>
''', encoding="utf-8")

colors = res / "values/colors.xml"
c = colors.read_text(encoding="utf-8")
if 'name="launcher_background"' in c:
    c = re.sub(r'(<color name="launcher_background">).*?(</color>)', r'\g<1>#071B32\g<2>', c, count=1)
else:
    c = c.replace("</resources>", '    <color name="launcher_background">#071B32</color>\n</resources>')
colors.write_text(c, encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
if 'versionCode = 55' not in g or 'versionName = "0.10.1"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 55', 'versionCode = 56', 1)
g = g.replace('versionName = "0.10.1"', 'versionName = "0.10.2"', 1)
gradle.write_text(g, encoding="utf-8")

print("MY EARTH v0.10.2 luminous globe and continuous-footstep launcher icon applied")
