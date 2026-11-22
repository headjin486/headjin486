from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

old_start = """                        menuDialog.dismiss()
                        if (which == 0) {"""
new_start = """                        menuDialog.dismiss()
                        // Wait until the parent AlertDialog has completed dismissal before
                        // presenting another window; avoids the child dialog being swallowed.
                        accountBackupButton.postDelayed({
                        if (which == 0) {"""
if old_start not in a:
    raise SystemExit("Expected account-menu dispatch start not found")
a = a.replace(old_start, new_start, 1)

old_end = """                        else if (which == 3) {
                            confirmAccountDeletion()
                        }
                    }
                    .show()"""
new_end = """                        else if (which == 3) {
                            confirmAccountDeletion()
                        }
                        }, 120L)
                    }
                    .show()"""
if old_end not in a:
    raise SystemExit("Expected account-menu dispatch end not found")
a = a.replace(old_end, new_end, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 90' not in g or 'versionName = "0.10.37"' not in g:
    raise SystemExit("Expected v0.10.37 / versionCode 90")
g = g.replace('versionCode = 90', 'versionCode = 91', 1)
g = g.replace('versionName = "0.10.37"', 'versionName = "0.10.38"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 90' not in v or 'versionName = "0.10.37"' not in v:
    raise SystemExit("Expected v0.10.37 verifier assertions")
v = v.replace('versionCode = 90', 'versionCode = 91', 1)
v = v.replace('versionName = "0.10.37"', 'versionName = "0.10.38"', 1)
anchor = 'assert "menuDialog.dismiss()" in menu'
if anchor not in v:
    raise SystemExit("Account menu verifier anchor missing")
v = v.replace(anchor, anchor + '''
assert "accountBackupButton.postDelayed({" in menu
assert "}, 120L)" in menu
''', 1)
verifier.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.38: defer account-menu actions until the parent dialog is fully dismissed.")
