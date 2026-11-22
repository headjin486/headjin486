from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# Dismiss the account action list before opening a follow-up dialog. This avoids
# the parent AlertDialog consuming/obscuring the child dialog on some Android
# versions and guarantees every selected action leaves the list cleanly.
start = a.find('setItems(arrayOf("클라우드 백업 설정 / 지금 백업"')
if start < 0:
    raise SystemExit("Four-item cloud/account menu not found")
end = a.find(")) { _, which ->", start)
if end < 0:
    raise SystemExit("Cloud/account menu selection listener not found")
if a.find("setItems(arrayOf(", start + 1) >= 0 and a.find("setItems(arrayOf(", start + 1) < end:
    raise SystemExit("Ambiguous nested account menu")
a = a[:end] + a[end:].replace(")) { _, which ->", ")) { menuDialog, which ->\n                        menuDialog.dismiss()", 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 87' not in g or 'versionName = "0.10.34"' not in g:
    raise SystemExit("Expected v0.10.34 / versionCode 87")
g = g.replace('versionCode = 87', 'versionCode = 88', 1)
g = g.replace('versionName = "0.10.34"', 'versionName = "0.10.35"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 87' not in v or 'versionName = "0.10.34"' not in v:
    raise SystemExit("Expected v0.10.34 verifier assertions")
v = v.replace('versionCode = 87', 'versionCode = 88', 1)
v = v.replace('versionName = "0.10.34"', 'versionName = "0.10.35"', 1)
anchor = 'assert "else if (which == 3)" in activity'
if anchor not in v:
    raise SystemExit("Account menu branch verifier anchor missing")
v = v.replace(anchor, anchor + '''
menu_start = activity.index('setItems(arrayOf("클라우드 백업 설정 / 지금 백업"')
menu_end = activity.index('.setNegativeButton("닫기", null)', menu_start)
menu = activity[menu_start:menu_end]
assert ")) { menuDialog, which ->" in menu
assert "menuDialog.dismiss()" in menu
''', 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.35: explicitly dismiss the account action list before opening selected follow-up dialogs.")
