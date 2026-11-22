from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
source = activity.read_text(encoding="utf-8")

old = 'Configuration.getInstance().userAgentValue = "EarthExplorer/0.7.6 (Android; $packageName)"'
new = 'Configuration.getInstance().userAgentValue = "MY EARTH/0.10.28 (Android; com.earthunlock.app; contact: headjin486@gmail.com)"'
if old not in source:
    if new not in source:
        raise SystemExit("Expected legacy OSM User-Agent or already-updated value not found; refusing unsafe replacement")
else:
    source = source.replace(old, new, 1)
activity.write_text(source, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 80' not in g or 'versionName = "0.10.27"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.27 / code 80")
g = g.replace('versionCode = 80', 'versionCode = 81', 1)
g = g.replace('versionName = "0.10.27"', 'versionName = "0.10.28"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += '''
# v0.10.28: identify the real MY EARTH app in OpenStreetMap tile requests.
grep -F 'MY EARTH/0.10.28 (Android; com.earthunlock.app; contact: headjin486@gmail.com)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'versionCode = 81' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.28"' app/build.gradle.kts >/dev/null
'''
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.28: OSM User-Agent updated; applicationId and data namespaces unchanged.")
