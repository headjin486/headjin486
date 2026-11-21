from pathlib import Path
import re, sys

root = Path(sys.argv[1])
# The percentage is rendered through the localized exploration_summary resource.
resources = {
    "app/src/main/res/values/strings.xml": ("My footsteps", "of the entire Earth map"),
    "app/src/main/res/values-ko/strings.xml": ("나의 발자취", "지구 전체 지도 대비"),
}
for relative, (anchor, suffix) in resources.items():
    path = root / relative
    xml = path.read_text(encoding="utf-8")
    pattern = r'(<string\s+name="exploration_summary"[^>]*>)(.*?)(</string>)'
    def update(m):
        value = m.group(2)
        if suffix in value:
            return m.group(0)
        if "%1$s" not in value:
            raise SystemExit(f"Percentage placeholder missing in {relative}")
        return m.group(1) + value.replace("%1$s", "%1$s (" + suffix + ")", 1) + m.group(3)
    updated, count = re.subn(pattern, update, xml, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"exploration_summary resource missing in {relative}")
    path.write_text(updated, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 56' not in g or 'versionName = "0.10.2"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 56', 'versionCode = 57', 1)
g = g.replace('versionName = "0.10.2"', 'versionName = "0.10.3"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.3 clarify the whole-Earth denominator in both localized summaries.
grep -F '지구 전체 지도 대비' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F 'of the entire Earth map' app/src/main/res/values/strings.xml >/dev/null
grep -F 'versionCode = 57' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.3"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.3 clarified map percentage denominator in localized summaries; calculation and user data unchanged")
