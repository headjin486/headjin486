from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# The first menu item has two states: if backup is enabled, show controls;
# otherwise, show the opt-in consent dialog. The old code incorrectly tested
# which == 1 inside the which == 0 branch, making the consent dialog unreachable.
outer = a.find("if (which == 0) {")
wrong = a.find("} else if (which == 1) {", outer)
next_branch = a.find("} else if (which == 1) {", wrong + 1)
if outer < 0 or wrong < 0 or next_branch < 0:
    raise SystemExit("Could not uniquely locate nested cloud-backup menu branch")
a = a[:wrong] + a[wrong:].replace("} else if (which == 1) {", "} else {", 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 89' not in g or 'versionName = "0.10.36"' not in g:
    raise SystemExit("Expected v0.10.36 / versionCode 89")
g = g.replace('versionCode = 89', 'versionCode = 90', 1)
g = g.replace('versionName = "0.10.36"', 'versionName = "0.10.37"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 89' not in v or 'versionName = "0.10.36"' not in v:
    raise SystemExit("Expected v0.10.36 verifier assertions")
v = v.replace('versionCode = 89', 'versionCode = 90', 1)
v = v.replace('versionName = "0.10.36"', 'versionName = "0.10.37"', 1)
anchor = 'assert "menuDialog.dismiss()" in menu'
if anchor not in v:
    raise SystemExit("Account menu verifier anchor missing")
v = v.replace(anchor, anchor + '''
cloud_action_start = menu.index("if (which == 0) {")
cloud_action_end = menu.index("} else if (which == 1) {", cloud_action_start)
cloud_action = menu[cloud_action_start:cloud_action_end]
assert "} else {" in cloud_action
assert "} else if (which == 1) {" not in cloud_action
''', 1)
verifier.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.37: restore the reachable cloud-backup opt-in dialog when backup is disabled.")
