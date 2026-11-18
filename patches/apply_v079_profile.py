from pathlib import Path
import sys

root = Path(sys.argv[1])
base = root / "app/src/main/java/com/example/earthexplorer"
activity = base / "MainActivity.kt"
s = activity.read_text(encoding="utf-8")

(base / "NicknameRules.kt").write_text(r'''package com.example.earthexplorer

/** Local nickname rules; server uniqueness and moderation are added with Firebase. */
object NicknameRules {
    private val allowed = Regex("^[\\p{L}\\p{N}_]{2,12}$")
    fun normalize(value: String): String = value.trim()
    fun isValid(value: String): Boolean = allowed.matches(normalize(value))
}
''', encoding="utf-8")

assert "import android.widget.Button\n" in s
s = s.replace("import android.widget.Button\n", "import android.widget.Button\nimport android.widget.EditText\n", 1)
assert "    private lateinit var currentMarker: Marker\n" in s
s = s.replace("    private lateinit var currentMarker: Marker\n",
              "    private lateinit var currentMarker: Marker\n    private lateinit var headerText: TextView\n", 1)

old = '''        val header = TextView(this).apply { text = "🌍  지구 탐험"; textSize = 23f; setTextColor(Color.WHITE); setPadding(20, 18, 20, 12) }
        root.addView(header)
'''
new = '''        headerText = TextView(this).apply {
            text = "🌍  지구 탐험"
            textSize = 23f
            setTextColor(Color.WHITE)
            setPadding(20, 18, 20, 12)
            isClickable = true
            isFocusable = true
            contentDescription = "탐험가 닉네임 설정"
            setOnClickListener { showNicknameDialog(required = false) }
        }
        root.addView(headerText)
'''
assert old in s
s = s.replace(old, new, 1)

old = '''        refreshTrackingStatus()
        refreshFog()
    }

    private fun requestAndStart() {
'''
new = '''        refreshTrackingStatus()
        refreshFog()
        updateNicknameHeader()
        if (savedNickname().isBlank()) showNicknameDialog(required = true)
    }

    private fun savedNickname(): String =
        getSharedPreferences("earth_unlock_profile", MODE_PRIVATE).getString("nickname", "").orEmpty()

    private fun updateNicknameHeader() {
        if (!::headerText.isInitialized) return
        val nickname = savedNickname()
        headerText.text = if (nickname.isBlank()) "🌍  지구 탐험 · 닉네임 설정" else "🌍  지구 탐험 · $nickname"
    }

    private fun showNicknameDialog(required: Boolean) {
        val input = EditText(this).apply {
            setSingleLine(true)
            hint = "2~12자 · 한글, 영문, 숫자, 밑줄"
            setText(savedNickname())
            filters = arrayOf(android.text.InputFilter.LengthFilter(12))
            inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
        }
        val builder = AlertDialog.Builder(this)
            .setTitle(if (required) "탐험가 닉네임 만들기" else "닉네임 변경")
            .setMessage("지도와 향후 세계 탐험 랭킹에 표시할 이름입니다. 닉네임은 2~12자로 입력해 주세요.")
            .setView(input)
            .setPositiveButton("저장", null)
        if (!required) builder.setNegativeButton("취소", null)
        val dialog = builder.create()
        dialog.setCancelable(!required)
        dialog.setCanceledOnTouchOutside(!required)
        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val nickname = NicknameRules.normalize(input.text?.toString().orEmpty())
                if (!NicknameRules.isValid(nickname)) {
                    input.error = "2~12자 한글·영문·숫자·밑줄만 사용할 수 있습니다."
                    return@setOnClickListener
                }
                getSharedPreferences("earth_unlock_profile", MODE_PRIVATE).edit()
                    .putString("nickname", nickname)
                    .apply()
                updateNicknameHeader()
                dialog.dismiss()
            }
        }
        dialog.show()
    }

    private fun requestAndStart() {
'''
assert old in s
s = s.replace(old, new, 1)
activity.write_text(s, encoding="utf-8")

test_dir = root / "app/src/test/java/com/example/earthexplorer"
test_dir.mkdir(parents=True, exist_ok=True)
(test_dir / "NicknameRulesTest.kt").write_text('''package com.example.earthexplorer

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NicknameRulesTest {
    @Test fun acceptsKoreanEnglishDigitsAndUnderscore() {
        assertTrue(NicknameRules.isValid("탐험가12"))
        assertTrue(NicknameRules.isValid("Earth_2026"))
    }

    @Test fun rejectsInvalidLengthAndWhitespace() {
        assertFalse(NicknameRules.isValid("A"))
        assertFalse(NicknameRules.isValid("abcdefghijklmn"))
        assertFalse(NicknameRules.isValid("지구 탐험"))
        assertFalse(NicknameRules.isValid(""))
    }
}
''', encoding="utf-8")

build = root / "app/build.gradle.kts"
g = build.read_text(encoding="utf-8")
assert 'versionCode = 32' in g and 'versionName = "0.7.8"' in g
g = g.replace('versionCode = 32', 'versionCode = 33', 1)
g = g.replace('versionName = "0.7.8"', 'versionName = "0.7.9"', 1)
build.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 32', 'versionCode = 33')
v = v.replace('versionName = "0.7.8"', 'versionName = "0.7.9"')
v += '''
# Nickname profile must be validated and persisted locally.
grep -F 'NicknameRules.isValid(nickname)' app/src/main/java/com/example/earthexplorer/MainActivity.kt >/dev/null
grep -F 'putString("nickname", nickname)' app/src/main/java/com/example/earthexplorer/MainActivity.kt >/dev/null
'''
verify.write_text(v, encoding="utf-8")
print("EARTH UNLOCK v0.7.9 nickname profile patch applied")
