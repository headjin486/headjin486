from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
a = activity.read_text(encoding="utf-8")

prop_anchor = "    private lateinit var countText: TextView\n"
if a.count(prop_anchor) != 1:
    raise SystemExit("Main dashboard badge property anchor missing")
a = a.replace(prop_anchor, prop_anchor + "    private var badgeCountButton: Button? = null\n    private var lastBadgeCountRefreshAt = 0L\n", 1)

button_anchor = '''        val badgesButton = Button(this).apply {
            text = "🏅 배지 " + badgeUnlockedCount + "/" + badgeList.size
            minWidth = dp(104)
            setOnClickListener { showBadges() }
            styleActionButton(this, primary = false, compact = true)
            contentDescription = "나의 배지 컬렉션, " + badgeUnlockedCount + "개 획득"
        }
'''
if a.count(button_anchor) != 1:
    raise SystemExit("Dashboard badge button construction anchor missing")
a = a.replace(button_anchor, button_anchor + "        badgeCountButton = badgesButton\n", 1)

receiver_anchor = '''            if (now - lastLiveFogRefreshAt >= 10_000L) {
                lastLiveFogRefreshAt = now
                refreshFog()
            }
'''
if a.count(receiver_anchor) != 1:
    raise SystemExit("Location update receiver anchor missing")
a = a.replace(receiver_anchor, receiver_anchor + "            refreshBadgeCount()\n", 1)

resume_anchor = '''        refreshFog()
        refreshTrackingStatus()
        FirebaseBackupManager.requestSyncIfEnabled(this, store)
'''
if a.count(resume_anchor) != 1:
    raise SystemExit("Activity resume refresh anchor missing")
a = a.replace(resume_anchor, '''        refreshFog()
        refreshTrackingStatus()
        refreshBadgeCount(force = true)
        FirebaseBackupManager.requestSyncIfEnabled(this, store)
''', 1)

method_anchor = "    private fun showBadges() {\n"
if a.count(method_anchor) != 1:
    raise SystemExit("Badge collection method insertion anchor missing")
method = '''    private fun refreshBadgeCount(force: Boolean = false) {
        val button = badgeCountButton ?: return
        val now = android.os.SystemClock.elapsedRealtime()
        if (!force && now - lastBadgeCountRefreshAt < 10_000L) return
        lastBadgeCountRefreshAt = now
        val badges = BadgeManager.badges(this, store)
        val unlocked = badges.count { it.unlocked }
        button.text = "🏅 배지 $unlocked/${badges.size}"
        button.contentDescription = "나의 배지 컬렉션, $unlocked개 획득"
    }

'''
a = a.replace(method_anchor, method + method_anchor, 1)

dismiss_anchor = '''        dialog.setOnShowListener {
            dialog.window?.setLayout(
                (resources.displayMetrics.widthPixels * 0.92f).toInt(),
                (resources.displayMetrics.heightPixels * 0.78f).toInt()
            )
        }
        dialog.show()
'''
if a.count(dismiss_anchor) != 1:
    raise SystemExit("Badge collection dialog display anchor missing")
a = a.replace(dismiss_anchor, '''        dialog.setOnShowListener {
            dialog.window?.setLayout(
                (resources.displayMetrics.widthPixels * 0.92f).toInt(),
                (resources.displayMetrics.heightPixels * 0.78f).toInt()
            )
        }
        dialog.setOnDismissListener { refreshBadgeCount(force = true) }
        dialog.show()
''', 1)

activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 88' not in g or 'versionName = "0.10.35"' not in g:
    raise SystemExit("Expected v0.10.35 / versionCode 88 before live badge count fix")
g = g.replace('versionCode = 88', 'versionCode = 89', 1)
g = g.replace('versionName = "0.10.35"', 'versionName = "0.10.36"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 88' not in v or 'versionName = "0.10.35"' not in v:
    raise SystemExit("Expected v0.10.35 release verifier assertions")
v = v.replace('versionCode = 88', 'versionCode = 89', 1)
v = v.replace('versionName = "0.10.35"', 'versionName = "0.10.36"', 1)
anchor = 'assert "menuDialog.dismiss()" in menu'
if anchor not in v:
    raise SystemExit("Account menu dismissal assertion anchor missing")
v = v.replace(anchor, anchor + ''' 
assert "private var badgeCountButton: Button? = null" in activity
assert "private fun refreshBadgeCount(force: Boolean = false)" in activity
assert 'button.text = "🏅 배지 $unlocked/${badges.size}"' in activity
assert "refreshBadgeCount()" in activity
assert "refreshBadgeCount(force = true)" in activity
assert "dialog.setOnDismissListener { refreshBadgeCount(force = true) }" in activity
''', 1)
verifier.write_text(v, encoding="utf-8")
print("MY EARTH v0.10.36: dashboard badge count refreshes from the same BadgeManager data as the collection, on location updates, app resume, and collection dismissal.")
