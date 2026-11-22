from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# The status dialog was the catch-all for every index other than 0 and 1.
# Narrow it to index 2 so index 3 opens only the deletion confirmation.
account_text = a.find("val accountText = when")
if account_text < 0:
    raise SystemExit("Account status block not found")
status_else = a.rfind("else {", 0, account_text)
if status_else < 0 or account_text - status_else > 500:
    raise SystemExit("Account status catch-all branch not found")
a = a[:status_else] + "else if (which == 2) {" + a[status_else + len("else {"):]

old_delete = "if (which == 3) {"
new_delete = "else if (which == 3) {"
if old_delete in a:
    a = a.replace(old_delete, new_delete, 1)
elif new_delete not in a:
    raise SystemExit("Account deletion branch not found")

menu_start = a.find("setItems(arrayOf(")
menu_end = a.find('.setNegativeButton("닫기", null)', menu_start)
if menu_start < 0 or menu_end < 0:
    raise SystemExit("Account menu block could not be isolated")
menu = a[menu_start:menu_end]
if "else if (which == 2)" not in menu or "else if (which == 3)" not in menu:
    raise SystemExit("Account menu is not a mutually exclusive 0/1/2/3 branch chain")
if "if (which == 3)" in menu:
    raise SystemExit("Independent deletion if still exists")
activity.write_text(a, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
v = v.replace('assert "if (which == 3) {\\n                            confirmAccountDeletion()" in activity',
              'assert "else if (which == 2)" in activity and "else if (which == 3)" in activity')
v = v.replace('assert "if (which == 2) {\\n                            confirmAccountDeletion()" not in activity',
              'assert "if (which == 3) {\\n                            confirmAccountDeletion()" not in activity')
v = v.replace("versionCode = 83", "versionCode = 84")
v = v.replace('versionName = "0.10.30"', 'versionName = "0.10.31"')
verifier.write_text(v, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 83' not in g or 'versionName = "0.10.30"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.30 / code 83")
g = g.replace('versionCode = 83', 'versionCode = 84', 1)
g = g.replace('versionName = "0.10.30"', 'versionName = "0.10.31"', 1)
gradle.write_text(g, encoding="utf-8")
print("MY EARTH v0.10.31: account status and account deletion now use mutually exclusive menu branches.")
