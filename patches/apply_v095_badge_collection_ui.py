from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

old_order = """        panel.addView(privacy, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        panel.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(4) })
"""
new_order = """        panel.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        panel.addView(privacy, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(4) })
"""
if old_order not in a:
    raise SystemExit("v0.9.4 menu order anchor missing")
a = a.replace(old_order, new_order, 1)

start = a.find("    private fun showBadges() {")
end = a.find("    private fun openAppSettings() {", start)
if start < 0 or end < 0:
    raise SystemExit("showBadges method boundaries missing")
method = r'''    private fun showBadges() {
        val badges = BadgeManager.badges(this, store)
        val unlocked = badges.count { it.unlocked }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(12), dp(18), dp(12))
        }

        val summary = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = android.view.Gravity.CENTER
            setPadding(dp(16), dp(16), dp(16), dp(16))
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(Color.rgb(31, 42, 58))
                cornerRadius = dp(18).toFloat()
                setStroke(dp(1), Color.rgb(74, 91, 112))
            }
        }
        summary.addView(TextView(this).apply {
            text = "나의 탐험 기록"
            textSize = 17f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
            gravity = android.view.Gravity.CENTER
        })
        summary.addView(TextView(this).apply {
            text = "$unlocked / ${badges.size} 개 획득"
            textSize = 23f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setTextColor(Color.rgb(255, 211, 112))
            gravity = android.view.Gravity.CENTER
            setPadding(0, dp(5), 0, dp(3))
        })
        summary.addView(TextView(this).apply {
            text = "걸을수록 새로운 기록과 메달이 쌓입니다."
            textSize = 12f
            setTextColor(Color.rgb(195, 207, 222))
            gravity = android.view.Gravity.CENTER
        })
        root.addView(summary, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(14) })

        badges.forEach { badge ->
            val gold = badge.unlocked
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                setPadding(dp(12), dp(12), dp(12), dp(12))
                background = android.graphics.drawable.GradientDrawable().apply {
                    setColor(if (gold) Color.rgb(39, 48, 59) else Color.rgb(29, 34, 43))
                    cornerRadius = dp(15).toFloat()
                    setStroke(dp(1), if (gold) Color.rgb(128, 101, 53) else Color.rgb(61, 69, 80))
                }
            }
            val medal = TextView(this).apply {
                text = if (gold) badge.icon else "🔒"
                textSize = 27f
                gravity = android.view.Gravity.CENTER
                setTextColor(Color.WHITE)
                background = android.graphics.drawable.GradientDrawable(
                    android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
                    if (gold) intArrayOf(Color.rgb(255, 220, 139), Color.rgb(176, 112, 35))
                    else intArrayOf(Color.rgb(86, 96, 109), Color.rgb(48, 57, 69))
                ).apply {
                    shape = android.graphics.drawable.GradientDrawable.OVAL
                    setStroke(dp(2), if (gold) Color.rgb(255, 237, 184) else Color.rgb(116, 127, 141))
                }
                elevation = dp(3).toFloat()
            }
            card.addView(medal, LinearLayout.LayoutParams(dp(58), dp(58)).apply {
                marginEnd = dp(13)
            })

            val detail = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            val titleRow = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
            }
            titleRow.addView(TextView(this).apply {
                text = badge.title
                textSize = 15f
                typeface = android.graphics.Typeface.DEFAULT_BOLD
                setTextColor(if (gold) Color.WHITE else Color.rgb(205, 211, 220))
            }, LinearLayout.LayoutParams(0, -2, 1f))
            titleRow.addView(TextView(this).apply {
                text = if (gold) "획득" else "도전 중"
                textSize = 10f
                typeface = android.graphics.Typeface.DEFAULT_BOLD
                setTextColor(if (gold) Color.rgb(255, 211, 112) else Color.rgb(154, 166, 181))
                setPadding(dp(7), dp(3), dp(7), dp(3))
                background = android.graphics.drawable.GradientDrawable().apply {
                    setColor(if (gold) Color.rgb(83, 66, 39) else Color.rgb(51, 60, 72))
                    cornerRadius = dp(9).toFloat()
                }
            })
            detail.addView(titleRow)
            detail.addView(TextView(this).apply {
                text = badge.description
                textSize = 12f
                setTextColor(Color.rgb(184, 195, 208))
                setPadding(0, dp(5), 0, 0)
                setLineSpacing(dp(2).toFloat(), 1f)
            })
            card.addView(detail, LinearLayout.LayoutParams(0, -2, 1f))
            root.addView(card, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(8) })
        }

        val scroll = android.widget.ScrollView(this).apply {
            isFillViewport = true
            addView(root)
        }
        val dialog = AlertDialog.Builder(this)
            .setTitle("🏆  나의 배지 컬렉션")
            .setView(scroll)
            .setPositiveButton("닫기", null)
            .create()
        dialog.setOnShowListener {
            dialog.window?.setLayout(
                (resources.displayMetrics.widthPixels * 0.92f).toInt(),
                (resources.displayMetrics.heightPixels * 0.78f).toInt()
            )
        }
        dialog.show()
    }

'''
a = a[:start] + method + a[end:]
activity.write_text(a, encoding="utf-8")

badge = pkg / "BadgeManager.kt"
b = badge.read_text(encoding="utf-8")
replacements = {
    '"처음으로 지도를 해금"': '"EARTH UNLOCK에서 처음으로 GPS 이동을 기록하고 주변 지도의 안개를 걷어내세요."',
    '"누적 1km 탐험"': '"누적 이동 거리 1km 달성. 첫 산책의 기록을 메달로 남깁니다."',
    '"누적 10km 탐험"': '"누적 이동 거리 10km 달성. 익숙한 길을 넘어 탐험가의 발걸음을 이어가세요."',
    '"누적 50km 탐험"': '"누적 이동 거리 50km 달성. 꾸준히 걸어 나만의 탐험 지도를 넓혀보세요."',
    '"누적 100km 탐험"': '"누적 이동 거리 100km 달성. 지구 여행자라 부를 만한 거리를 기록했습니다."',
    '"누적 500km 탐험"': '"누적 이동 거리 500km 달성. 긴 여정으로 대탐험가의 자격을 증명하세요."',
    '"누적 해금 면적 1km²"': '"GPS 이동으로 누적 1km² 이상의 지도 영역을 새롭게 밝혀내세요."',
    '"누적 해금 면적 10km²"': '"누적 해금 면적 10km² 달성. 안개 너머의 세상이 넓어지고 있습니다."',
    '"누적 해금 면적 50km²"': '"누적 해금 면적 50km² 달성. 넓은 영역을 개척한 탐험의 증표입니다."',
    '"서로 다른 날 3일 탐험"': '"하루의 기록에 그치지 않고, 서로 다른 날짜에 3일 탐험을 기록하세요."',
    '"서로 다른 날 7일 탐험"': '"서로 다른 날짜에 7일 탐험 달성. 일주일의 꾸준함을 기념합니다."',
    '"서로 다른 날 30일 탐험"': '"서로 다른 날짜에 30일 탐험 달성. 한 달간 이어진 여정의 메달입니다."',
    '"첫 번째 탐험 구역 해금"': '"새로운 지도 구역을 처음으로 방문해 나만의 탐험 영역을 만드세요."',
    '"서로 다른 5개 구역 해금"': '"서로 다른 탐험 구역 5곳을 방문해 지도 위 활동 반경을 넓히세요."',
    '"서로 다른 10개 구역 해금"': '"서로 다른 탐험 구역 10곳을 방문해 대륙을 누비는 탐험가가 되어보세요."',
    '"처음으로 고향 국가 밖의 지도 해금"': '"기준 국가 밖의 다른 나라에서 GPS 이동으로 새로운 지도를 밝혀내세요."',
    '"고향 국가 외 2개 국가 탐험"': '"기준 국가를 제외한 서로 다른 해외 국가 2곳에서 탐험 기록을 남기세요."',
    '"고향 국가 외 5개 국가 탐험"': '"기준 국가를 제외한 서로 다른 해외 국가 5곳을 탐험해 세계 탐험가에 도전하세요."'
}
for old, new in replacements.items():
    if old not in b:
        raise SystemExit("Badge description anchor missing: " + old)
    b = b.replace(old, new, 1)
badge.write_text(b, encoding="utf-8")
print("EARTH UNLOCK v0.9.5 badge collection UI patch applied")
