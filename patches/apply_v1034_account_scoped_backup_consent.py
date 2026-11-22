from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# Declining the post-link cloud-backup prompt must revoke any previously stored
# device-level opt-in. Otherwise an earlier anonymous-account consent could
# silently carry over to a different Google UID.
old = '.setNegativeButton("계정 연결만 유지", null)'
new = '''.setNegativeButton("계정 연결만 유지") { _, _ ->
                FirebaseBackupManager.setEnabled(this, false)
            }'''
if a.count(old) != 1:
    raise SystemExit("Expected exactly one cloud opt-in decline action")
a = a.replace(old, new, 1)

# A restore action switches Firebase UID. Clear the device-level backup flag
# before signing out so automatic sync cannot upload to the selected Google UID
# before the user accepts the separate backup consent prompt.
restore_start = a.find("if (requestCode == 9205) {")
restore_end = a.find("} else {", restore_start)
if restore_start < 0 or restore_end < 0:
    raise SystemExit("Google restore branch not found")
restore = a[restore_start:restore_end]
if restore.count("auth.signOut()") != 1:
    raise SystemExit("Expected one signOut in the Google restore branch")
if "FirebaseBackupManager.setEnabled(this, false)" not in restore:
    restore = restore.replace(
        "auth.signOut()",
        "FirebaseBackupManager.setEnabled(this, false)\n                auth.signOut()",
        1
    )
a = a[:restore_start] + restore + a[restore_end:]
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 86' not in g or 'versionName = "0.10.33"' not in g:
    raise SystemExit("Expected v0.10.33 / versionCode 86 before consent fix")
g = g.replace('versionCode = 86', 'versionCode = 87', 1)
g = g.replace('versionName = "0.10.33"', 'versionName = "0.10.34"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 86' not in v or 'versionName = "0.10.33"' not in v:
    raise SystemExit("Expected v0.10.33 release verifier assertions")
v = v.replace('versionCode = 86', 'versionCode = 87', 1)
v = v.replace('versionName = "0.10.33"', 'versionName = "0.10.34"', 1)
anchor = 'assert google_flow.count("confirmCloudBackupOptIn()") >= 3'
if anchor not in v:
    raise SystemExit("Cloud consent flow assertion not found")
v = v.replace(anchor, anchor + '''
assert '.setNegativeButton("계정 연결만 유지") { _, _ ->' in consent
assert 'FirebaseBackupManager.setEnabled(this, false)' in consent
restore_start = google_flow.index("if (requestCode == 9205) {")
restore_end = google_flow.index("} else {", restore_start)
restore = google_flow[restore_start:restore_end]
assert restore.index("FirebaseBackupManager.setEnabled(this, false)") < restore.index("auth.signOut()")
''', 1)
verifier.write_text(v, encoding="utf-8")
print("v0.10.34 clears stale backup consent when declining and before switching to a different Google UID.")
