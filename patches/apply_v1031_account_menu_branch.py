from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

status_branch = """                        } else {
                            val user = com.google.firebase.auth.FirebaseAuth.getInstance().currentUser
                            val accountText = when {
"""
fixed_status = """                        } else if (which == 2) {
                            val user = com.google.firebase.auth.FirebaseAuth.getInstance().currentUser
                            val accountText = when {
"""
if status_branch in a:
    a = a.replace(status_branch, fixed_status, 1)
elif fixed_status not in a:
    raise SystemExit("Account status catch-all branch not found; refusing unsafe patch")

old_tail = """                        }
                        if (which == 3) {
                            confirmAccountDeletion()
                        }
"""
new_tail = """                        } else if (which == 3) {
                            confirmAccountDeletion()
                        }
"""
if old_tail in a:
    a = a.replace(old_tail, new_tail, 1)
elif new_tail not in a:
    raise SystemExit("Account deletion branch tail not found; refusing unsafe patch")

menu_start = a.find("setItems(arrayOf(")
menu_end = a.find(".setNegativeButton(\"닫기\", null)", menu_start)
if menu_start < 0 or menu_end < 0:
    raise SystemExit("Account menu block could not be isolated")
menu = a[menu_start:menu_end]
if "else if (which == 2)" not in menu or "else if (which == 3)" not in menu:
    raise SystemExit("Account menu is not a complete 0/1/2/3 branch chain")
if "if (which == 3)" in menu:
    raise SystemExit("Old independent deletion if still exists")
activity.write_text(a, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
anchor = 'assert "if (which == 3) {\\n                            confirmAccountDeletion()" in activity'
if anchor not in v:
    raise SystemExit("Strict verifier deletion assertion anchor not found")
v = v.replace(anchor, '''assert "else if (which == 2)" in activity
assert "else if (which == 3)" in activity
assert "if (which == 3) {\\n                            confirmAccountDeletion()" not in activity''', 1)
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
