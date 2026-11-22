from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

old = '''                } else {
                    Toast.makeText(
                        this@MainActivity,
                        "계정 삭제를 완료하지 못했습니다: ${message ?: "잠시 후 다시 시도하거나 문의 이메일로 요청해 주세요."}",
                        Toast.LENGTH_LONG
                    ).show()
                }
'''
new = '''                } else {
                    // Stop automatic sync after any deletion failure so deleted backup chunks
                    // cannot be silently recreated while the account-removal request is pending.
                    FirebaseBackupManager.setEnabled(this@MainActivity, false)
                    Toast.makeText(
                        this@MainActivity,
                        "계정 삭제를 완료하지 못했습니다. 클라우드 자동 백업은 중지했습니다: ${message ?: "문의 이메일로 삭제를 요청해 주세요."}",
                        Toast.LENGTH_LONG
                    ).show()
                }
'''
if old not in a:
    raise SystemExit("Account deletion failure branch not found; refusing unsafe edit")
a = a.replace(old, new, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 85' not in g or 'versionName = "0.10.32"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.32 / code 85")
g = g.replace('versionCode = 85', 'versionCode = 86', 1)
g = g.replace('versionName = "0.10.32"', 'versionName = "0.10.33"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 85' not in v or 'versionName = "0.10.32"' not in v:
    raise SystemExit("Unexpected release verifier version assertions")
v = v.replace("versionCode = 85", "versionCode = 86", 1)
v = v.replace('versionName = "0.10.32"', 'versionName = "0.10.33"', 1)
anchor = 'assert "headjin486@gmail.com" in manager'
if anchor not in v:
    raise SystemExit("Account deletion support-email assertion not found")
v = v.replace(anchor, anchor + '''
assert "FirebaseBackupManager.setEnabled(this@MainActivity, false)" in activity
assert "클라우드 자동 백업은 중지했습니다" in activity
''', 1)
verifier.write_text(v, encoding="utf-8")
print("v0.10.33 disables automatic cloud backup after any account-deletion failure to prevent deleted chunks from being recreated.")
