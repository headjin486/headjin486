from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

old_count = "        panel.addView(countText)\\n"
if a.count(old_count) != 1:
    raise SystemExit("Exploration summary anchor missing or ambiguous")
a = a.replace(old_count, "", 1)

old_badge_block = """        val badgesButton = Button(this).apply {
            text = "🏅  나의 배지"
            setOnClickListener { showBadges() }
            styleActionButton(this, primary = false, compact = true)
        }
        footerRow.addView(privacy, LinearLayout.LayoutParams(0, dp(34), 1f).apply {
            marginStart = dp(5)
        })
        panel.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        panel.addView(footerRow, LinearLayout.LayoutParams(-1, dp(34)).apply { topMargin = dp(8) })
"""
new_badge_block = """        val badgeList = BadgeManager.badges(this, store)
        val badgeUnlockedCount = badgeList.count { it.unlocked }
        val badgesButton = Button(this).apply {
            text = "🏅 배지 " + badgeUnlockedCount + "/" + badgeList.size
            minWidth = dp(104)
            setOnClickListener { showBadges() }
            styleActionButton(this, primary = false, compact = true)
            contentDescription = "나의 배지 컬렉션, " + badgeUnlockedCount + "개 획득"
        }
        val summaryRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        summaryRow.addView(countText, LinearLayout.LayoutParams(0, -2, 1f))
        summaryRow.addView(badgesButton, LinearLayout.LayoutParams(-2, dp(40)).apply {
            marginStart = dp(8)
        })
        footerRow.addView(privacy, LinearLayout.LayoutParams(0, dp(34), 1f).apply {
            marginStart = dp(5)
        })
        panel.addView(summaryRow, 0)
        panel.addView(footerRow, LinearLayout.LayoutParams(-1, dp(34)).apply { topMargin = dp(8) })
"""
if old_badge_block not in a:
    raise SystemExit("v0.9.7 badge/footer placement anchor missing")
a = a.replace(old_badge_block, new_badge_block, 1)
activity.write_text(a, encoding="utf-8")

fog = pkg / "FogOverlay.kt"
f = fog.read_text(encoding="utf-8")
needle = "        xfermode = android.graphics.PorterDuffXfermode(android.graphics.PorterDuff.Mode.CLEAR)\\n"
if f.count(needle) != 1:
    raise SystemExit("Reveal erase-paint anchor missing or ambiguous")
f = f.replace(needle, needle + "        maskFilter = android.graphics.BlurMaskFilter(3.5f, android.graphics.BlurMaskFilter.Blur.NORMAL)\\n", 1)
fog.write_text(f, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 53' not in g or 'versionName = "0.9.9"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 53', 'versionCode = 54', 1)
g = g.replace('versionName = "0.9.9"', 'versionName = "0.10.0"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.10.0 balanced summary/badge row and feathered reveal edges.
grep -F 'panel.addView(summaryRow, 0)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'BlurMaskFilter(3.5f' app/src/main/java/com/earthunlock/app/FogOverlay.kt >/dev/null
grep -F 'versionCode = 54' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.0"' app/build.gradle.kts >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.10.0 balanced menu and feathered reveal-edge patch applied")
