from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Replace the text-heavy location pill with a compact, accessible floating control.
old = """        val locate = Button(this).apply {
            text = getString(R.string.current_location_button)
            setOnClickListener { goToCurrentLocation() }
            styleActionButton(this, primary = false, floating = true)
        }
"""
new = """        val locate = Button(this).apply {
            text = "⌖"
            contentDescription = getString(R.string.current_location_button)
            textSize = 25f
            isAllCaps = false
            setTextColor(Color.rgb(35, 126, 245))
            setOnClickListener { goToCurrentLocation() }
            minWidth = dp(46)
            minimumWidth = dp(46)
            minHeight = dp(46)
            minimumHeight = dp(46)
            setPadding(0, 0, 0, dp(2))
            background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(Color.WHITE)
                setStroke(dp(1), Color.rgb(226, 233, 241))
            }
            elevation = dp(5).toFloat()
            stateListAnimator = null
        }
"""
if old not in s: raise SystemExit("Styled locate button block not found")
s=s.replace(old,new,1)

# Make compass a matching circular icon button, with no text label occupying map space.
old = """        val compassReset = Button(this).apply {
            text = "N ↑"
            textSize = 11f
            isAllCaps = false
            minWidth = 0
            minimumWidth = 0
            setPadding(10, 4, 10, 4)
            setTextColor(Color.rgb(10, 31, 58))
            contentDescription = "지도 방향을 북쪽으로 초기화"
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(Color.WHITE)
                cornerRadius = 22f
                setStroke(1, Color.LTGRAY)
            }
            elevation = 5f
"""
new = """        val compassReset = Button(this).apply {
            text = "N"
            textSize = 13f
            isAllCaps = false
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.BOLD)
            minWidth = dp(42)
            minimumWidth = dp(42)
            minHeight = dp(42)
            minimumHeight = dp(42)
            setPadding(0, 0, 0, 0)
            setTextColor(Color.rgb(10, 31, 58))
            contentDescription = "지도 방향을 북쪽으로 초기화"
            background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.OVAL
                setColor(Color.WHITE)
                setStroke(dp(1), Color.rgb(226, 233, 241))
            }
            elevation = dp(5).toFloat()
            stateListAnimator = null
"""
if old not in s: raise SystemExit("Compass style block not found")
s=s.replace(old,new,1)

# Keep a consistent 10dp visual gap between the two floating controls on opposite corners.
s=s.replace("topMargin = 18\n            marginStart = 16", "topMargin = 18\n            marginStart = 16",1)

activity.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
if 'versionCode = 41' not in g or 'versionName = "0.8.7"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g=g.replace('versionCode = 41','versionCode = 42',1).replace('versionName = "0.8.7"','versionName = "0.8.8"',1)
gradle.write_text(g,encoding="utf-8")
verify=root/"scripts/verify-service-lifecycle.sh"
v=verify.read_text(encoding="utf-8").replace('versionCode = 41','versionCode = 42').replace('versionName = "0.8.7"','versionName = "0.8.8"')
v += """
# Compact floating location and compass controls.
grep -F 'contentDescription = getString(R.string.current_location_button)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'text = "⌖"' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'text = "N"' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
"""
verify.write_text(v,encoding="utf-8")
print("EARTH UNLOCK v0.8.8 minimalist location and compass controls patch applied")
