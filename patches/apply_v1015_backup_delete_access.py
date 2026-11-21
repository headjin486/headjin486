from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# The enabled-state dialog already has a cloud-delete neutral action; remove its later
# duplicate neutral "Close" call, which would otherwise override the delete action.
a = a.replace('                        .setNeutralButton("닫기", null)\n                        .show()', '                        .show()', 1)

disabled_anchor = '                        .setNegativeButton("나중에", null)\n                        .setPositiveButton("동의하고 켜기")'
if "MY_EARTH_DELETE_CLOUD_WHEN_DISABLED" not in a:
    if disabled_anchor not in a:
        raise SystemExit("Disabled cloud-backup dialog insertion point missing")
    replacement = '''                        .setNegativeButton("나중에", null)
                        .setNeutralButton("클라우드 백업 데이터 삭제") { _, _ ->
                            AlertDialog.Builder(this@MainActivity)
                                .setTitle("클라우드 백업 삭제")
                                .setMessage("서버에 저장된 해금 지도 셀 백업을 삭제합니다. 휴대폰 내부의 GPS 기록과 지도 데이터는 삭제되지 않습니다.")
                                .setNegativeButton("취소", null)
                                .setPositiveButton("삭제") { _, _ ->
                                    FirebaseBackupManager.deleteCloudBackup { success ->
                                        Toast.makeText(this@MainActivity, if (success) "클라우드 백업 데이터를 삭제했습니다." else "삭제하지 못했습니다. 네트워크 연결 후 다시 시도하세요.", Toast.LENGTH_LONG).show()
                                    }
                                }
                                .show()
                        }
                        .setPositiveButton("동의하고 켜기")'''
    a = a.replace(disabled_anchor, replacement, 1)
activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 67' not in g or 'versionName = "0.10.14"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 67', 'versionCode = 68', 1).replace('versionName = "0.10.14"', 'versionName = "0.10.15"', 1)
gradle.write_text(g, encoding="utf-8")
print("Made cloud backup deletion available when backup is enabled or disabled; bumped to v0.10.15.")
