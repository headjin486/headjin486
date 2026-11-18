from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

# Remove the permanent language button; language is a first-launch choice only.
old_menu = '''        val language = Button(this).apply {
            text = getString(R.string.language)
            setOnClickListener { showLanguageDialog() }
        }
        row2.addView(settings, LinearLayout.LayoutParams(0, -2, 1f))
        row2.addView(language, LinearLayout.LayoutParams(0, -2, 1f))
'''
if old_menu not in s:
    raise SystemExit("Expected language settings row not found")
s = s.replace(old_menu, '''        row2.addView(settings, LinearLayout.LayoutParams(-1, -2, 1f))
''', 1)

old_nickname = '        if (savedNickname().isBlank()) showNicknameDialog(required = true)'
if s.count(old_nickname) != 1:
    raise SystemExit("Expected exactly one first-run nickname prompt")
s = s.replace(old_nickname, '''        val languageSaved = getSharedPreferences("app_settings", MODE_PRIVATE)
            .contains("app_language")
        if (!languageSaved) {
            showLanguageDialog(firstLaunch = true)
        } else if (savedNickname().isBlank()) {
            showNicknameDialog(required = true)
        }''', 1)

old_method = '''    private fun showLanguageDialog() {
        val options = arrayOf(
            getString(R.string.language_system),
            getString(R.string.language_korean),
            getString(R.string.language_english)
        )
        val values = arrayOf(AppLocale.SYSTEM, AppLocale.KOREAN, AppLocale.ENGLISH)
        val prefs = getSharedPreferences("app_settings", MODE_PRIVATE)
        val current = prefs.getString("app_language", AppLocale.SYSTEM) ?: AppLocale.SYSTEM
        val selected = values.indexOf(current).coerceAtLeast(0)
        AlertDialog.Builder(this)
            .setTitle(R.string.language_dialog_title)
            .setSingleChoiceItems(options, selected) { dialog, which ->
                prefs.edit().putString("app_language", values[which]).apply()
                dialog.dismiss()
                recreate()
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

'''
if old_method not in s:
    raise SystemExit("Existing language dialog method not found")
new_method = '''    private fun showLanguageDialog(firstLaunch: Boolean) {
        val options = arrayOf(
            getString(R.string.language_system),
            getString(R.string.language_korean),
            getString(R.string.language_english)
        )
        val values = arrayOf(AppLocale.SYSTEM, AppLocale.KOREAN, AppLocale.ENGLISH)
        val prefs = getSharedPreferences("app_settings", MODE_PRIVATE)
        val current = prefs.getString("app_language", AppLocale.SYSTEM) ?: AppLocale.SYSTEM
        val selected = values.indexOf(current).coerceAtLeast(0)
        val builder = AlertDialog.Builder(this)
            .setTitle(R.string.language_dialog_title)
            .setSingleChoiceItems(options, selected) { dialog, which ->
                prefs.edit().putString("app_language", values[which]).apply()
                dialog.dismiss()
                recreate()
            }
        if (!firstLaunch) builder.setNegativeButton(R.string.cancel, null)
        val dialog = builder.create()
        if (firstLaunch) {
            dialog.setCancelable(false)
            dialog.setCanceledOnTouchOutside(false)
        }
        dialog.show()
    }

'''
s = s.replace(old_method, new_method, 1)
activity.write_text(s, encoding="utf-8")

# Keep the choice inside the app, not duplicated in Android's system app-language page.
manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
m = m.replace('        android:localeConfig="@xml/locales_config"\n', '')
manifest.write_text(m, encoding="utf-8")

# Bump the release version for this behavior change.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 35' not in g or 'versionName = "0.8.1"' not in g:
    raise SystemExit("Unexpected base version; refusing unsafe version bump")
g = g.replace('versionCode = 35', 'versionCode = 36', 1)
g = g.replace('versionName = "0.8.1"', 'versionName = "0.8.2"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 35', 'versionCode = 36')
v = v.replace('versionName = "0.8.1"', 'versionName = "0.8.2"')
v = v.replace('grep -F \'android:localeConfig="@xml/locales_config"\' app/src/main/AndroidManifest.xml >/dev/null',
              '! grep -F \'android:localeConfig=\' app/src/main/AndroidManifest.xml >/dev/null')
v += '''
# Language is selected once on first launch and is not exposed as a persistent menu.
grep -F 'showLanguageDialog(firstLaunch = true)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'contains("app_language")' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
! grep -F 'setOnClickListener { showLanguageDialog' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
'''
verify.write_text(v, encoding="utf-8")

print("EARTH UNLOCK v0.8.2 first-launch-only language selection applied")
