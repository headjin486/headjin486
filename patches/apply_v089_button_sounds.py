from pathlib import Path
import sys

root=Path(sys.argv[1])
activity=root/"app/src/main/java/com/earthunlock/app/MainActivity.kt"
s=activity.read_text(encoding="utf-8")

# A single lightweight system tone generator; no audio assets or background service.
field_anchor="class MainActivity : Activity() {"
if field_anchor not in s: raise SystemExit("MainActivity class declaration missing")
s=s.replace(field_anchor,field_anchor+"""
    private var uiTone: android.media.ToneGenerator? = null

    private fun playUiTone(tone: Int, durationMs: Int) {
        val generator = uiTone ?: android.media.ToneGenerator(
            android.media.AudioManager.STREAM_SYSTEM, 28
        ).also { uiTone = it }
        generator.startTone(tone, durationMs)
    }
""",1)

# Attach cleanup to the Activity's existing lifecycle method; do not declare a duplicate.
on_destroy_anchor="    override fun onDestroy() {"
if on_destroy_anchor not in s: raise SystemExit("Existing onDestroy lifecycle method missing")
s=s.replace(on_destroy_anchor,on_destroy_anchor+"""
        uiTone?.release()
        uiTone = null
""",1)

# Add a short, restrained location confirmation sound on tap.
locate_anchor='''            setOnClickListener { goToCurrentLocation() }
'''
if locate_anchor not in s: raise SystemExit("Location click listener missing")
s=s.replace(locate_anchor,'''            setOnClickListener {
                playUiTone(android.media.ToneGenerator.TONE_PROP_BEEP, 55)
                goToCurrentLocation()
            }
''',1)

# The compass uses the slightly more musical two-tone acknowledgement.
compass_anchor='''            setOnClickListener {
                map.setMapOrientation(0f)
'''
if compass_anchor not in s: raise SystemExit("Compass click listener missing")
s=s.replace(compass_anchor,'''            setOnClickListener {
                playUiTone(android.media.ToneGenerator.TONE_PROP_ACK, 90)
                map.setMapOrientation(0f)
''',1)

activity.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
if 'versionCode = 42' not in g or 'versionName = "0.8.8"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g=g.replace('versionCode = 42','versionCode = 43',1).replace('versionName = "0.8.8"','versionName = "0.8.9"',1)
gradle.write_text(g,encoding="utf-8")
verify=root/"scripts/verify-service-lifecycle.sh"
v=verify.read_text(encoding="utf-8").replace('versionCode = 42','versionCode = 43').replace('versionName = "0.8.8"','versionName = "0.8.9"')
v=v.replace("grep -F 'refreshLatestSavedPosition()' app/src/main/java/com/earthunlock/app/MainActivity.kt | grep -F 'onResume' >/dev/null || true", "sed -n '/override fun onResume()/,/^    }/p' app/src/main/java/com/example/earthexplorer/MainActivity.kt | grep -F 'refreshLatestSavedPosition()' >/dev/null")
v=v.replace("app/src/main/java/com/earthunlock/app/LocationTrackingService.kt", "app/src/main/java/com/earthunlock/app/LocationTrackingService.kt")
v=v.replace("app/src/main/java/com/example/earthexplorer/MainActivity.kt", "app/src/main/java/com/earthunlock/app/MainActivity.kt")
verify.write_text(v,encoding="utf-8")
print("EARTH UNLOCK v0.8.9 concise location and compass feedback sounds patch applied")
