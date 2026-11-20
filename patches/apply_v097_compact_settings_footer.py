from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

old = """        val row2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        val settings = Button(this).apply {
            text = getString(R.string.location_permission_settings)
            setOnClickListener { openAppSettings() }
            styleActionButton(this, primary = false, compact = true)
        }
        row2.addView(settings, LinearLayout.LayoutParams(-1, -2, 1f))
        val privacy = Button(this).apply {
            text = getString(R.string.privacy_policy)
            setOnClickListener { startActivity(Intent(this@MainActivity, PrivacyPolicyActivity::class.java)) }
            styleActionButton(this, primary = false, compact = true, quiet = true)
        }
"""
new = """        val footerRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        val settings = Button(this).apply {
            text = getString(R.string.location_permission_settings)
            setOnClickListener { openAppSettings() }
            styleActionButton(this, primary = false, compact = true, quiet = true)
        }
        footerRow.addView(settings, LinearLayout.LayoutParams(0, dp(34), 1f).apply {
            marginEnd = dp(5)
        })
        val privacy = Button(this).apply {
            text = getString(R.string.privacy_policy)
            setOnClickListener { startActivity(Intent(this@MainActivity, PrivacyPolicyActivity::class.java)) }
            styleActionButton(this, primary = false, compact = true, quiet = true)
        }
        footerRow.addView(privacy, LinearLayout.LayoutParams(0, dp(34), 1f).apply {
            marginStart = dp(5)
        })
"""
if old not in s:
    raise SystemExit("Footer menu construction anchor missing")
s = s.replace(old, new, 1)

old = """        panel.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        panel.addView(row2, LinearLayout.LayoutParams(-1, dp(44)).apply { topMargin = dp(8) })
        panel.addView(privacy, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(4) })
"""
new = """        panel.addView(badgesButton, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        panel.addView(footerRow, LinearLayout.LayoutParams(-1, dp(34)).apply { topMargin = dp(8) })
"""
if old not in s:
    raise SystemExit("Footer menu placement anchor missing")
s = s.replace(old, new, 1)
activity.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 50' not in g or 'versionName = "0.9.6"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 50', 'versionCode = 51', 1)
g = g.replace('versionName = "0.9.6"', 'versionName = "0.9.7"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += """
# v0.9.7 compact side-by-side settings footer.
grep -F 'val footerRow = LinearLayout(this)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'footerRow.addView(settings' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'footerRow.addView(privacy' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'panel.addView(footerRow' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.9.7 compact settings footer patch applied")
