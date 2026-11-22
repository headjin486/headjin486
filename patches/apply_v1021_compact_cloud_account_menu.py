from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# Keep the existing actions and their confirmation flows, but remove the two
# full-width rows that consume valuable map height.
for line in (
    "        panel.addView(cloudBackupButton, LinearLayout.LayoutParams(-1, -2))",
    "        panel.addView(googleRecoveryButton, LinearLayout.LayoutParams(-1, -2))",
):
    if a.count(line) != 1:
        raise SystemExit("Expected exactly one cloud/account full-width row; refusing unsafe layout change")
    a = a.replace(line + "\n", "", 1)

anchor = """        summaryRow.addView(countText, LinearLayout.LayoutParams(0, -2, 1f))
        summaryRow.addView(badgesButton, LinearLayout.LayoutParams(-2, dp(40)).apply {
            marginStart = dp(8)
        })
"""
replacement = """        summaryRow.addView(countText, LinearLayout.LayoutParams(0, -2, 1f))
        // Compact action stack: badges remain visible, with one combined cloud/account entry below.
        val accountToolsColumn = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }
        accountToolsColumn.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(36)))
        val accountBackupButton = Button(this).apply {
            text = "☁ 백업 · 계정"
            isAllCaps = false
            minWidth = 0
            setPadding(dp(8), 0, dp(8), 0)
            styleActionButton(this, primary = false, compact = true)
            contentDescription = "클라우드 백업 및 Google 계정 관리"
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("백업 및 계정 관리")
                    .setItems(arrayOf("클라우드 백업 설정 / 지금 백업", "Google 계정 연결 / 기기 변경 복원")) { _, which ->
                        if (which == 0) {
                            if (FirebaseBackupManager.isEnabled(this@MainActivity)) {
                                AlertDialog.Builder(this@MainActivity)
                                    .setTitle("클라우드 백업")
                                    .setMessage("해금된 지도 셀만 Firebase에 백업합니다. GPS 좌표와 시간순 이동 경로는 전송하지 않습니다.")
                                    .setNegativeButton("백업 끄기") { _, _ ->
                                        FirebaseBackupManager.setEnabled(this@MainActivity, false)
                                        text = "☁ 백업 · 계정"
                                    }
                                    .setPositiveButton("지금 백업") { _, _ ->
                                        FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true) { message ->
                                            runOnUiThread {
                                                Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
                                            }
                                        }
                                    }
                                    .setNeutralButton("닫기", null)
                                    .show()
                            } else {
                                AlertDialog.Builder(this@MainActivity)
                                    .setTitle("탐험 기록 클라우드 백업")
                                    .setMessage("동의하면 해금된 지도 셀 식별자만 Firebase에 백업됩니다. GPS 좌표, 이동 경로, 위치 기록과 시간 정보는 업로드하지 않습니다. 앱 데이터 삭제나 기기 변경 전에 Google 계정 복구 기능을 연결해야 합니다.")
                                    .setNegativeButton("나중에", null)
                                    .setPositiveButton("동의하고 켜기") { _, _ ->
                                        FirebaseBackupManager.setEnabled(this@MainActivity, true)
                                        text = "☁ 백업 · 계정"
                                        FirebaseBackupManager.requestSyncIfEnabled(this@MainActivity, store, true) { message ->
                                            runOnUiThread {
                                                Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
                                            }
                                        }
                                    }
                                    .show()
                            }
                        } else {
                            AlertDialog.Builder(this@MainActivity)
                                .setTitle("Google 계정으로 기록 보호")
                                .setMessage("현재 휴대폰에서는 익명 계정을 Google 계정에 연결해 기기 변경에 대비할 수 있습니다. 새 휴대폰에서는 기존 Google 계정으로 로그인해 클라우드 기록을 복원할 수 있습니다.")
                                .setPositiveButton("현재 기록을 Google에 연결") { _, _ ->
                                    startGoogleRecoveryFlow(restoreExisting = false)
                                }
                                .setNeutralButton("기존 Google 계정으로 복원") { _, _ ->
                                    startGoogleRecoveryFlow(restoreExisting = true)
                                }
                                .setNegativeButton("취소", null)
                                .show()
                        }
                    }
                    .setNegativeButton("닫기", null)
                    .show()
            }
        }
        accountToolsColumn.addView(accountBackupButton, LinearLayout.LayoutParams(-1, dp(34)).apply {
            topMargin = dp(3)
        })
        summaryRow.addView(accountToolsColumn, LinearLayout.LayoutParams(dp(132), -2).apply {
            marginStart = dp(8)
        })
"""
if a.count(anchor) != 1:
    raise SystemExit("Summary/badge row anchor not found exactly once")
a = a.replace(anchor, replacement, 1)

# Verify that the old controls are no longer added as full-width panel rows.
if "panel.addView(cloudBackupButton" in a or "panel.addView(googleRecoveryButton" in a:
    raise SystemExit("Old full-width cloud/account rows remain")
if "accountToolsColumn.addView(badgesButton" not in a or "accountToolsColumn.addView(accountBackupButton" not in a:
    raise SystemExit("Compact action stack verification failed")

activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 73' not in g or 'versionName = "0.10.20"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.20")
g = g.replace('versionCode = 73', 'versionCode = 74', 1)
g = g.replace('versionName = "0.10.20"', 'versionName = "0.10.21"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.21 compact cloud/account action below the badge button.
grep -F 'accountToolsColumn.addView(badgesButton' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'accountToolsColumn.addView(accountBackupButton' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
! grep -F 'panel.addView(cloudBackupButton' app/src/main/java/com/earthunlock/app/MainActivity.kt
! grep -F 'panel.addView(googleRecoveryButton' app/src/main/java/com/earthunlock/app/MainActivity.kt
grep -F 'versionCode = 74' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.21"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.21 compact cloud/account menu layout applied.")
