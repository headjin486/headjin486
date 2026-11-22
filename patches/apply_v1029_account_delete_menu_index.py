from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# The real menu has four entries: backup (0), Google recovery (1),
# backup/account status (2), and deletion (3). Keep deletion at index 3.
expected = "if (which == 3) {\n                            confirmAccountDeletion()"
wrong = "if (which == 2) {\n                            confirmAccountDeletion()"
if expected not in a:
    if wrong in a:
        a = a.replace(wrong, expected, 1)
    else:
        raise SystemExit("Account deletion menu branch not found; refusing unsafe patch")
activity.write_text(a, encoding="utf-8")

verify = root / "scripts/verify-play-release-policy.py"
verify.parent.mkdir(parents=True, exist_ok=True)
verify.write_text(r'''from pathlib import Path
import re

activity = Path("app/src/main/java/com/earthunlock/app/MainActivity.kt").read_text(encoding="utf-8")
manager = Path("app/src/main/java/com/earthunlock/app/FirebaseBackupManager.kt").read_text(encoding="utf-8")
gradle = Path("app/build.gradle.kts").read_text(encoding="utf-8")
manifest = Path("app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

menu = re.search(r"setItems\\(arrayOf\\((.*?)\\)\\)\\s*\\{\\s*_,\\s*which\\s*->", activity, re.S)
assert menu, "Account menu array not found"
entries = re.findall(r'"([^"]+)"', menu.group(1))
assert entries == [
    "클라우드 백업 설정 / 지금 백업",
    "Google 계정 연결 / 기기 변경 복원",
    "계정 및 백업 상태 확인",
    "계정 및 클라우드 데이터 삭제",
], f"Unexpected account menu entries/order: {entries}"
assert "if (which == 0)" in activity
assert "else if (which == 1)" in activity
assert "if (which == 3) {\\n                            confirmAccountDeletion()" in activity
assert "if (which == 2) {\\n                            confirmAccountDeletion()" not in activity

assert "private fun confirmAccountDeletion()" in activity
assert "private fun performAccountDeletion()" in activity
assert "fun deleteAccountAndCloudData" in manager
assert manager.index("Tasks.whenAll(batches)") < manager.index("user.delete()")
assert 'collection("exploration_backups").document(user.uid).collection("chunks")' in manager
assert 'versionCode = 82' in gradle
assert 'versionName = "0.10.29"' in gradle
assert 'android:usesCleartextTraffic="false"' in manifest
assert "ACCESS_BACKGROUND_LOCATION" not in manifest
print("MY EARTH release policy checks passed: four account menu entries, deletion index, deletion order, version, and manifest.")
''', encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 81' not in g or 'versionName = "0.10.28"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.28")
g = g.replace('versionCode = 81', 'versionCode = 82', 1)
g = g.replace('versionName = "0.10.28"', 'versionName = "0.10.29"', 1)
gradle.write_text(g, encoding="utf-8")
print("MY EARTH v0.10.29: preserved correct account deletion menu index and added strict release-policy verification.")
