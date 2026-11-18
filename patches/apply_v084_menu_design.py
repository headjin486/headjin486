from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# A compact, consistent visual system: one primary action, restrained secondary actions.
old = '''        val locate = Button(this).apply {
            text = getString(R.string.current_location_button); textSize = 13f; isAllCaps = false
            setTextColor(Color.rgb(10, 31, 58)); setOnClickListener { goToCurrentLocation() }
            background = android.graphics.drawable.GradientDrawable().apply { setColor(Color.WHITE); cornerRadius = 28f; setStroke(1, Color.LTGRAY) }
            elevation = 8f
        }
'''
new = '''        val locate = Button(this).apply {
            text = getString(R.string.current_location_button)
            setOnClickListener { goToCurrentLocation() }
            styleActionButton(this, primary = false, floating = true)
        }
'''
if old not in s: raise SystemExit("Locate button block not found")
s = s.replace(old, new, 1)

old = '''        val row1 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        val start = Button(this).apply { text = getString(R.string.explore_start); setOnClickListener { requestAndStart() } }
        val stop = Button(this).apply { text = getString(R.string.explore_stop); setOnClickListener { stopService(Intent(this@MainActivity, LocationTrackingService::class.java)); refreshFog() } }
        row1.addView(start, LinearLayout.LayoutParams(0, -2, 1f)); row1.addView(stop, LinearLayout.LayoutParams(0, -2, 1f))
        val row2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        val settings = Button(this).apply { text = getString(R.string.location_permission_settings); setOnClickListener { openAppSettings() } }
        row2.addView(settings, LinearLayout.LayoutParams(-1, -2, 1f))
        val privacy = Button(this).apply {
            text = getString(R.string.privacy_policy)
            setOnClickListener { startActivity(Intent(this@MainActivity, PrivacyPolicyActivity::class.java)) }
        }
        panel.addView(row1); panel.addView(row2); panel.addView(privacy); root.addView(panel); setContentView(root)
'''
new = '''        val row1 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        val start = Button(this).apply {
            text = getString(R.string.explore_start)
            setOnClickListener { requestAndStart() }
            styleActionButton(this, primary = true)
        }
        val stop = Button(this).apply {
            text = getString(R.string.explore_stop)
            setOnClickListener { stopService(Intent(this@MainActivity, LocationTrackingService::class.java)); refreshFog() }
            styleActionButton(this, primary = false)
        }
        row1.addView(start, LinearLayout.LayoutParams(0, dp(50), 1f).apply { marginEnd = dp(6) })
        row1.addView(stop, LinearLayout.LayoutParams(0, dp(50), 1f).apply { marginStart = dp(6) })
        val row2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
        val settings = Button(this).apply {
            text = getString(R.string.location_permission_settings)
            setOnClickListener { openAppSettings() }
            styleActionButton(this, primary = false, compact = true)
        }
        row2.addView(settings, LinearLayout.LayoutParams(-1, dp(44)))
        val privacy = Button(this).apply {
            text = getString(R.string.privacy_policy)
            setOnClickListener { startActivity(Intent(this@MainActivity, PrivacyPolicyActivity::class.java)) }
            styleActionButton(this, primary = false, compact = true, quiet = true)
        }
        val row1Params = row1.layoutParams as? LinearLayout.LayoutParams
        panel.addView(row1)
        panel.addView(row2, LinearLayout.LayoutParams(-1, dp(44)).apply { topMargin = dp(8) })
        panel.addView(privacy, LinearLayout.LayoutParams(-1, dp(40)).apply { topMargin = dp(2) })
        root.addView(panel); setContentView(root)
'''
if old not in s: raise SystemExit("Menu button layout block not found")
s = s.replace(old, new, 1)

# Add reusable style helpers before requestAndStart().
needle = '    private fun requestAndStart() {'
helpers = '''    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun styleActionButton(
        button: Button,
        primary: Boolean,
        floating: Boolean = false,
        compact: Boolean = false,
        quiet: Boolean = false
    ) {
        val fill = when {
            floating -> Color.WHITE
            primary -> Color.rgb(54, 145, 255)
            quiet -> Color.TRANSPARENT
            else -> Color.rgb(22, 49, 76)
        }
        val text = if (floating) Color.rgb(8, 29, 51) else if (primary) Color.WHITE else Color.rgb(205, 221, 237)
        val stroke = if (quiet) Color.rgb(49, 75, 101) else fill
        button.apply {
            isAllCaps = false
            textSize = if (compact) 12f else 14f
            setTextColor(text)
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            minHeight = dp(if (floating) 46 else if (compact) 40 else 50)
            minimumHeight = minHeight
            minWidth = 0
            setPadding(dp(if (compact) 10 else 14), 0, dp(if (compact) 10 else 14), 0)
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(fill)
                cornerRadius = dp(if (floating) 24 else 14).toFloat()
                setStroke(dp(1), stroke)
            }
            elevation = dp(if (floating) 5 else 0).toFloat()
            stateListAnimator = null
        }
    }

'''
if needle not in s: raise SystemExit("Helper insertion point missing")
s = s.replace(needle, helpers + needle, 1)

# Keep the panel compact and create breathing room between summary and actions.
s = s.replace('setPadding(18, 12, 18, 18); setBackgroundColor(Color.rgb(10, 31, 58))',
              'setPadding(16, 10, 16, 12); setBackgroundColor(Color.rgb(8, 27, 48))', 1)
s = s.replace('textSize = 18f; setTextColor(Color.WHITE); setPadding(2, 4, 2, 12)',
              'textSize = 17f; setTextColor(Color.WHITE); setPadding(2, 2, 2, 8)', 1)
s = s.replace('textSize = 15f; setTextColor(Color.rgb(255, 210, 90)); setPadding(2, 0, 2, 10)',
              'textSize = 13f; setTextColor(Color.rgb(139, 196, 255)); setPadding(2, 0, 2, 8)', 1)

activity.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 37' not in g or 'versionName = "0.8.3"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 37', 'versionCode = 38', 1)
g = g.replace('versionName = "0.8.3"', 'versionName = "0.8.4"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 37', 'versionCode = 38')
v = v.replace('versionName = "0.8.3"', 'versionName = "0.8.4"')
v += '''
# Compact action button system must be used by all primary map actions.
grep -F 'styleActionButton(this, primary = true)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'styleActionButton(this, primary = false, floating = true)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'private fun styleActionButton(' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
'''
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.8.4 compact menu design patch applied")
