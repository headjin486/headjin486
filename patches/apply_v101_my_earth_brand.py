from pathlib import Path
import re, sys

root = Path(sys.argv[1])
res = root / "app/src/main/res"
gradle = root / "app/build.gradle.kts"
manifest = root / "app/src/main/AndroidManifest.xml"
pkg = root / "app/src/main/java/com/earthunlock/app"

# Localized app identity and recording-first terminology.
translations = {
    "values/strings.xml": {
        "app_name": "MY EARTH",
        "header_title": "MY EARTH",
        "brand_tagline": "YOUR FOOTSTEPS. YOUR WORLD.",
        "explore_start": "Start recording",
        "explore_stop": "Stop recording",
        "exploration_summary": "👣 My footsteps\\n%1$s\\nRecorded area %2$s",
        "tracking_active": "● Recording footsteps · GPS location is being saved",
        "tracking_inactive": "● Recording stopped",
        "tracking_channel_name": "MY EARTH location recording",
        "tracking_notification_title": "MY EARTH is recording your footsteps",
        "tracking_notification_text": "Your walked route is being added to your personal map.",
        "tracking_notification_stop": "Stop recording",
        "nickname_header": "MY EARTH · %1$s",
        "nickname_header_empty": "MY EARTH · Set nickname",
        "privacy_title": "MY EARTH Privacy Notice",
    },
    "values-ko/strings.xml": {
        "app_name": "MY EARTH",
        "header_title": "MY EARTH",
        "brand_tagline": "내가 걸어온 길, 나만의 지도가 되다.",
        "explore_start": "기록 시작",
        "explore_stop": "기록 종료",
        "exploration_summary": "👣 나의 발자취\\n%1$s\\n기록된 영역 %2$s",
        "tracking_active": "● 발자취 기록 중 · GPS 위치 저장 중",
        "tracking_inactive": "● 기록 중지됨",
        "tracking_channel_name": "MY EARTH 위치 기록",
        "tracking_notification_title": "MY EARTH 발자취 기록 중",
        "tracking_notification_text": "걸어온 길을 나만의 지도에 기록하고 있습니다.",
        "tracking_notification_stop": "기록 중지",
        "nickname_header": "MY EARTH · %1$s",
        "nickname_header_empty": "MY EARTH · 닉네임 설정",
        "privacy_title": "MY EARTH 개인정보 처리 안내",
    },
}

def set_string(xml, key, value, required=True):
    pattern = re.compile(r'(<string\s+name="' + re.escape(key) + r'"[^>]*>).*?(</string>)', re.S)
    updated, count = pattern.subn(lambda m: m.group(1) + value + m.group(2), xml, count=1)
    if count == 0:
        if required:
            raise SystemExit(f"Required string resource missing: {key}")
        return xml
    return updated

for relative, values in translations.items():
    path = res / relative
    xml = path.read_text(encoding="utf-8")
    for key, value in values.items():
        xml = set_string(xml, key, value, required=(key != "brand_tagline"))
    if 'name="brand_tagline"' not in xml:
        xml = xml.replace("</resources>", f'    <string name="brand_tagline">{values["brand_tagline"]}</string>\\n</resources>')
    # Reframe the consent disclosure around personal route recording, not game-like unlocking.
    xml = xml.replace("자동 탐험", "자동 기록").replace("탐험 기록", "발자취 기록")
    xml = xml.replace("지나간 주변을 지도에 공개합니다", "걸어온 길 주변을 나만의 지도에 기록합니다")
    xml = xml.replace("automatic exploration", "automatic recording")
    xml = xml.replace("exploration data", "footstep records")
    xml = xml.replace("reveal nearby areas", "record the areas around your route")
    path.write_text(xml, encoding="utf-8")

# Add a restrained brand tagline below the existing title.
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")
anchor = "        map = MapView(this).apply {"
if anchor not in a:
    raise SystemExit("MainActivity map placement anchor missing")
tagline = """        val brandTagline = TextView(this).apply {
            text = getString(R.string.brand_tagline)
            textSize = 10.5f
            letterSpacing = 0.08f
            setTextColor(Color.rgb(167, 220, 203))
            setPadding(dp(20), 0, dp(20), dp(9))
        }
        root.addView(brandTagline)
"""
a = a.replace(anchor, tagline + anchor, 1)
a = a.replace("나의 탐험 기록", "나의 발자취 기록")
activity.write_text(a, encoding="utf-8")

# Refined MY EARTH adaptive launcher icon: globe outline + one continuous route.
icon = res / "drawable/ic_launcher_foreground.xml"
icon.write_text(r'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="@android:color/transparent"
        android:strokeColor="#A7DCCB"
        android:strokeWidth="3.2"
        android:strokeLineCap="round"
        android:pathData="M54,14 A40,40 0,1 1,53.9 14" />
    <path
        android:fillColor="@android:color/transparent"
        android:strokeColor="#527D7A"
        android:strokeWidth="1.8"
        android:pathData="M18,54 H90 M54,14 C37,26 37,82 54,94 M54,14 C71,26 71,82 54,94" />
    <path
        android:fillColor="@android:color/transparent"
        android:strokeColor="#A7DCCB"
        android:strokeWidth="4.2"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:pathData="M29,69 C37,69 38,54 47,54 S58,66 65,53 S75,37 81,37" />
    <path android:fillColor="#FFFFFF" android:pathData="M25,65a4.5,4.5 0,1 0,9 0a4.5,4.5 0,1 0,-9 0" />
    <path android:fillColor="#A7DCCB" android:pathData="M76,37a5,5 0,1 0,10 0a5,5 0,1 0,-10 0" />
</vector>
''', encoding="utf-8")

colors = res / "values/colors.xml"
c = colors.read_text(encoding="utf-8")
c = re.sub(r'(<color name="launcher_background">).*?(</color>)', r'\g<1>#142B35\g<2>', c, count=1)
colors.write_text(c, encoding="utf-8")

styles = res / "values/styles.xml"
st = styles.read_text(encoding="utf-8")
st = st.replace("#63E879", "#A7DCCB").replace("#07172D", "#142B35")
styles.write_text(st, encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
if 'android:label="@string/app_name"' not in m:
    raise SystemExit("Manifest app label is not resource-backed; refusing package/identity changes")
manifest.write_text(m, encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
if 'versionCode = 54' not in g or 'versionName = "0.10.0"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 54', 'versionCode = 55', 1)
g = g.replace('versionName = "0.10.0"', 'versionName = "0.10.1"', 1)
gradle.write_text(g, encoding="utf-8")

# Verify the data-preserving Android identity and the new visual/brand resources.
verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.1 MY EARTH identity; keep applicationId, database and preference namespaces unchanged.
grep -F 'applicationId = "com.earthunlock.app"' app/build.gradle.kts >/dev/null
grep -F 'versionCode = 55' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.1"' app/build.gradle.kts >/dev/null
grep -F '<string name="app_name">MY EARTH</string>' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F '<string name="brand_tagline">내가 걸어온 길, 나만의 지도가 되다.</string>' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F 'strokeColor="#A7DCCB"' app/src/main/res/drawable/ic_launcher_foreground.xml >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.1 brand identity, recording-first copy and adaptive icon applied")
