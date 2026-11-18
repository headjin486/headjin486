from pathlib import Path
import re, shutil, sys

root = Path(sys.argv[1])
old_pkg = "com.example.earthexplorer"
new_pkg = "com.earthunlock.app"
old_dir = root / "app/src/main/java/com/example/earthexplorer"
new_dir = root / "app/src/main/java/com/earthunlock/app"
assert old_dir.exists(), f"Expected source package directory: {old_dir}"

# Move Kotlin sources and tests to the permanent Play Store package.
new_dir.parent.mkdir(parents=True, exist_ok=True)
shutil.move(str(old_dir), str(new_dir))
old_test = root / "app/src/test/java/com/example/earthexplorer"
new_test = root / "app/src/test/java/com/earthunlock/app"
if old_test.exists():
    new_test.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_test), str(new_test))

for base in [root / "app", root / "scripts"]:
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix not in {".kt", ".kts", ".xml", ".sh"}:
            continue
        try:
            value = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = value.replace(old_pkg, new_pkg).replace("com/example/earthexplorer", "com/earthunlock/app")
        if updated != value:
            path.write_text(updated, encoding="utf-8")

build = root / "app/build.gradle.kts"
g = build.read_text(encoding="utf-8")
assert 'namespace = "com.earthunlock.app"' in g
assert 'applicationId = "com.earthunlock.app"' in g
assert 'versionCode = 34' in g and 'versionName = "0.8.0"' in g
g = g.replace('versionCode = 34', 'versionCode = 35', 1)
g = g.replace('versionName = "0.8.0"', 'versionName = "0.8.1"', 1)
build.write_text(g, encoding="utf-8")

res = root / "app/src/main/res"
(res / "values").mkdir(parents=True, exist_ok=True)
(res / "values-ko").mkdir(parents=True, exist_ok=True)

english = r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">EARTH UNLOCK</string>
    <string name="header_title">🌍  EARTH UNLOCK</string>
    <string name="current_location_button">◎ My location</string>
    <string name="osm_attribution_desc">OpenStreetMap attribution and license information</string>
    <string name="current_location_marker">Current location</string>
    <string name="explore_start">Start exploring</string>
    <string name="explore_stop">Stop exploring</string>
    <string name="location_permission_settings">Location permissions</string>
    <string name="privacy_policy">Privacy policy</string>
    <string name="language">Language</string>
    <string name="location_disclosure_title">Location data use</string>
    <string name="location_disclosure_body">When you start automatic exploration, GPS location is used to show your position and reveal nearby areas on the map. Location and exploration data are stored in this app on your device. Tracking continues while you use another screen until you stop it, and an Android foreground-service notification is shown. On Android 13 and later, if notification permission is denied, the service may appear in the system task manager instead of the notification shade. Map-area requests may be sent to the map tile provider to display the map. Account synchronization is not available in this version.</string>
    <string name="cancel">Cancel</string>
    <string name="agree_start">Agree and start</string>
    <string name="tracking_requested">● Exploration start requested · waiting for GPS</string>
    <string name="tracking_failed">Could not start exploration. Check location permission and device settings.</string>
    <string name="permission_required_title">Precise location permission required</string>
    <string name="permission_required_body">Precise location is required to reveal the exploration map at approximately 10-meter accuracy. Allow Precise location in app settings, then try again.</string>
    <string name="open_app_settings">Open app settings</string>
    <string name="close">Close</string>
    <string name="current_location_unavailable">Could not determine your current location. Start automatic exploration and try again.</string>
    <string name="exploration_summary">🌍 Earth explored\n%1$s\nUnlocked area %2$s</string>
    <string name="map_load_failed">Could not load map data. Please try again shortly.</string>
    <string name="tracking_active">● Exploring · receiving and recording GPS location</string>
    <string name="tracking_inactive">● Exploration stopped</string>
    <string name="tracking_channel_name">EARTH UNLOCK location tracking</string>
    <string name="tracking_notification_title">EARTH UNLOCK is exploring</string>
    <string name="tracking_notification_text">Automatically revealing the area around your route.</string>
    <string name="tracking_notification_stop">Stop exploring</string>
    <string name="language_dialog_title">Choose app language</string>
    <string name="language_system">Follow device language</string>
    <string name="language_korean">한국어</string>
    <string name="language_english">English</string>
    <string name="nickname_accessibility">Set explorer nickname</string>
    <string name="nickname_header">🌍  EARTH UNLOCK · %1$s</string>
    <string name="nickname_header_empty">🌍  EARTH UNLOCK · Set nickname</string>
    <string name="nickname_hint">2–12 characters · letters, numbers, underscore</string>
    <string name="nickname_create_title">Create explorer nickname</string>
    <string name="nickname_change_title">Change nickname</string>
    <string name="nickname_message">This name will appear on the map and future global exploration rankings. Enter 2–12 characters.</string>
    <string name="save">Save</string>
    <string name="nickname_invalid">Use 2–12 Korean or English letters, numbers, or underscores.</string>
    <string name="privacy_title">EARTH UNLOCK Privacy Notice</string>
    <string name="privacy_body">Effective date: 2026-11-14\nOperator and privacy inquiries: [Enter developer name and contact email before release]\n\n1. Information processed\nWhile automatic exploration is enabled with your consent, GPS location (latitude and longitude), location accuracy, and measurement time are processed to show your position and calculate explored map cells.\n\n2. Purposes\nThis information is used to display your current position, calculate routes and distance, and save revealed map areas and exploration statistics.\n\n3. Storage and retention\nGPS records and explored cells are stored in the app's private SQLite database on this Android device. This version does not provide account-based server synchronization. Local records are deleted when app data is cleared or the app is uninstalled. Android automatic backup is disabled.\n\n4. External services\nThis version does not include advertising or analytics SDKs. Map tiles based on OpenStreetMap are requested over the network. The tile provider may process network information such as IP address, requested map area, and access time. The app does not separately send GPS coordinates to the map provider, but requested tiles can reveal the map area being viewed. Check the provider's current terms and privacy notice before release.\n\n5. Your choices\nAutomatic exploration requires precise location permission. You can stop recording with the in-app Stop exploring control or the persistent notification. You can revoke location permission or clear app data in Android settings.\n\n6. Security and contact\nRecords are stored in app-private storage and Android automatic backup is disabled. Device-level security risks cannot be completely eliminated. Contact the operator listed above for privacy inquiries.\n\n[Required before release] Replace the operator and contact placeholders, verify this notice against the actual release build and map provider, and publish a public privacy-policy URL. This draft is not a substitute for legal review.</string>
</resources>
'''
korean = r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">EARTH UNLOCK</string>
    <string name="header_title">🌍  지구 탐험</string>
    <string name="current_location_button">◎ 내 위치</string>
    <string name="osm_attribution_desc">OpenStreetMap 저작자 표시 및 라이선스 안내 열기</string>
    <string name="current_location_marker">현재 위치</string>
    <string name="explore_start">자동 탐험 시작</string>
    <string name="explore_stop">탐험 중지</string>
    <string name="location_permission_settings">위치 권한 설정</string>
    <string name="privacy_policy">개인정보 처리방침</string>
    <string name="language">언어 설정</string>
    <string name="location_disclosure_title">위치 정보 사용 안내</string>
    <string name="location_disclosure_body">자동 탐험을 켜면 이동 중 GPS 위치를 수집해 현재 위치를 표시하고 지나간 주변을 지도에 공개합니다. 위치와 탐험 기록은 이 기기의 앱 내부 데이터베이스에 저장됩니다. 다른 화면을 사용하더라도 사용자가 중지할 때까지 위치 기록이 계속되며 Android 포그라운드 서비스 알림이 표시됩니다. Android 13 이상에서 알림 권한을 거부한 경우 알림 창 대신 시스템 작업 관리자에 표시될 수 있습니다. 지도를 표시하기 위해 지도 제공자에 지도 영역 요청이 전송될 수 있습니다. 현재 버전은 계정 동기화 기능을 제공하지 않습니다.</string>
    <string name="cancel">취소</string>
    <string name="agree_start">동의하고 시작</string>
    <string name="tracking_requested">● 탐험 시작 요청됨 · GPS 연결 확인 중</string>
    <string name="tracking_failed">탐험을 시작하지 못했습니다. 위치 권한과 기기 설정을 확인하세요.</string>
    <string name="permission_required_title">정확한 위치 권한이 필요합니다</string>
    <string name="permission_required_body">약 10m 범위의 탐험 지도를 만들려면 정확한 위치 권한이 필요합니다. 설정에서 정확한 위치 권한을 허용한 뒤 다시 시작해 주세요.</string>
    <string name="open_app_settings">앱 설정 열기</string>
    <string name="close">닫기</string>
    <string name="current_location_unavailable">현재 위치를 확인하지 못했습니다. 자동 탐험을 시작해 주세요.</string>
    <string name="exploration_summary">🌍 지구 탐험률\n%1$s\n공개 면적 %2$s</string>
    <string name="map_load_failed">지도 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</string>
    <string name="tracking_active">● 자동 탐험 중 · GPS 위치 수신/기록 중</string>
    <string name="tracking_inactive">● 탐험 중지됨</string>
    <string name="tracking_channel_name">지구 탐험 위치 기록</string>
    <string name="tracking_notification_title">지구 탐험 기록 중</string>
    <string name="tracking_notification_text">이동 경로 주변을 자동으로 탐험하고 있습니다.</string>
    <string name="tracking_notification_stop">탐험 중지</string>
    <string name="language_dialog_title">앱 언어 선택</string>
    <string name="language_system">기기 언어 따라가기</string>
    <string name="language_korean">한국어</string>
    <string name="language_english">English</string>
    <string name="nickname_accessibility">탐험가 닉네임 설정</string>
    <string name="nickname_header">🌍  지구 탐험 · %1$s</string>
    <string name="nickname_header_empty">🌍  지구 탐험 · 닉네임 설정</string>
    <string name="nickname_hint">2~12자 · 한글, 영문, 숫자, 밑줄</string>
    <string name="nickname_create_title">탐험가 닉네임 만들기</string>
    <string name="nickname_change_title">닉네임 변경</string>
    <string name="nickname_message">지도와 향후 세계 탐험 랭킹에 표시할 이름입니다. 닉네임은 2~12자로 입력해 주세요.</string>
    <string name="save">저장</string>
    <string name="nickname_invalid">2~12자 한글·영문·숫자·밑줄만 사용할 수 있습니다.</string>
    <string name="privacy_title">지구 탐험 개인정보 처리 안내</string>
    <string name="privacy_body">시행일: 2026-11-14\n운영자 및 개인정보 문의: [출시 전 개발자명과 연락 이메일 입력]\n\n1. 처리하는 정보\n사용자가 자동 탐험을 시작하고 안내에 동의한 동안 GPS 위치(위도·경도), 위치 정확도, 측정 시각을 처리합니다. 이를 이용해 현재 위치를 표시하고 탐험한 지도 격자를 계산합니다.\n\n2. 처리 목적\n현재 위치 표시, 이동 경로 및 누적 이동거리 계산, 방문한 지도 영역의 공개 상태와 탐험 통계 저장을 위해 사용합니다.\n\n3. 저장 위치 및 보유 기간\nGPS 기록과 탐험 격자는 기본적으로 Android 기기 내부의 앱 전용 SQLite 데이터베이스에 저장됩니다. 현재 버전은 계정 기반 서버 동기화 기능을 제공하지 않습니다. 앱 데이터 삭제 또는 앱 제거 시 로컬 기록이 삭제됩니다. 앱 자동 백업은 비활성화되어 있습니다.\n\n4. 외부 서비스\n현재 버전에는 광고·분석 SDK가 포함되어 있지 않습니다. 지도 표시를 위해 OpenStreetMap 기반 지도 타일을 네트워크로 요청합니다. 지도 타일 제공자는 요청 과정에서 IP 주소, 요청한 지도 영역, 접속 시각 등 네트워크 정보를 처리할 수 있습니다. 앱은 GPS 좌표를 별도로 지도 제공자에게 전송하지 않지만, 요청한 타일은 이용자가 보고 있는 지도 영역을 드러낼 수 있습니다. 실제 출시 전 지도 타일 제공자의 최신 약관과 개인정보 안내를 확인해야 합니다.\n\n5. 이용자의 선택과 통제\n정확한 위치 권한을 허용하지 않으면 자동 탐험 기능을 사용할 수 없습니다. 이용자는 앱의 탐험 중지 버튼 또는 지속 알림의 중지 동작으로 위치 기록을 중단할 수 있습니다. Android 설정에서 위치 권한을 철회하거나 앱 데이터를 삭제할 수 있습니다.\n\n6. 보안 및 문의\n기록은 앱 전용 내부 저장소에 보관하며 Android 자동 백업을 비활성화했습니다. 기기 자체의 보안 위험까지 완전히 방지할 수는 없습니다. 개인정보 관련 문의는 위 운영자 연락처로 접수할 수 있습니다.\n\n[출시 전 필수] 대괄호의 운영자·연락처를 실제 정보로 교체하고, 실제 배포 버전의 동작 및 지도 제공자와 대조한 뒤 공개 개인정보처리방침 URL을 게시해야 합니다. 이 화면은 초안이며 법률 검토를 대체하지 않습니다.</string>
</resources>
'''
english = english.replace("'", "’")
(res / "values" / "strings.xml").write_text(english, encoding="utf-8")
(res / "values-ko" / "strings.xml").write_text(korean, encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:label="지구 탐험"', 'android:label="@string/app_name"')
manifest.write_text(m, encoding="utf-8")

locale_file = new_dir / "AppLocale.kt"
locale_file.write_text(r'''package com.earthunlock.app

import android.content.Context
import android.content.res.Configuration
import java.util.Locale

/** Per-app language preference. "system" follows the device; unsupported device locales fall back to English. */
internal object AppLocale {
    const val SYSTEM = "system"
    const val KOREAN = "ko"
    const val ENGLISH = "en"

    fun wrap(base: Context): Context {
        val selected = base.getSharedPreferences("app_settings", Context.MODE_PRIVATE)
            .getString("app_language", SYSTEM) ?: SYSTEM
        val locale = when (selected) {
            KOREAN -> Locale.forLanguageTag(KOREAN)
            ENGLISH -> Locale.forLanguageTag(ENGLISH)
            else -> {
                val system = if (android.os.Build.VERSION.SDK_INT >= 24)
                    base.resources.configuration.locales[0]
                else @Suppress("DEPRECATION") base.resources.configuration.locale
                if (system.language == KOREAN) Locale.forLanguageTag(KOREAN)
                else Locale.forLanguageTag(ENGLISH)
            }
        }
        Locale.setDefault(locale)
        val configuration = Configuration(base.resources.configuration)
        configuration.setLocale(locale)
        return base.createConfigurationContext(configuration)
    }
}
''', encoding="utf-8")

activity = new_dir / "MainActivity.kt"
s = activity.read_text(encoding="utf-8")
# Apply locale before Activity inflates any UI.
needle = '    override fun onCreate(savedInstanceState: Bundle?) {'
assert needle in s
s = s.replace(needle, '''    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

'''+needle, 1)

replacements = {
    'text = "🌍  지구 탐험"': 'text = getString(R.string.header_title)',
    'text = "◎ 내 위치"': 'text = getString(R.string.current_location_button)',
    'contentDescription = "OpenStreetMap 저작자 표시 및 라이선스 안내 열기"': 'contentDescription = getString(R.string.osm_attribution_desc)',
    'text = "자동 탐험 시작"': 'text = getString(R.string.explore_start)',
    'text = "탐험 중지"': 'text = getString(R.string.explore_stop)',
    'text = "위치 권한 설정"': 'text = getString(R.string.location_permission_settings)',
    'text = "개인정보 처리방침"': 'text = getString(R.string.privacy_policy)',
    'title = "현재 위치"': 'title = getString(R.string.current_location_marker)',
    '.setTitle("위치 정보 사용 안내")': '.setTitle(R.string.location_disclosure_title)',
    '            .setMessage(\n                "자동 탐험을 켜면 이동 중 GPS 위치를 수집해 현재 위치를 표시하고, 지나간 주변을 지도에 공개합니다. " +\n                    "위치와 탐험 기록은 이 기기의 앱 내부 데이터베이스에 저장됩니다. " +\n                    "앱을 다른 화면으로 전환해도 사용자가 중지할 때까지 위치 기록이 계속되며, 시스템 포그라운드 서비스 알림이 표시됩니다. Android 13 이상에서 알림 권한을 거부한 경우 알림 창에는 보이지 않고 시스템 작업 관리자에 표시될 수 있습니다. " +\n                    "지도 타일을 불러오기 위해 지도 제공자에 지도 영역 요청이 전송될 수 있습니다. " +\n                    "현재 MVP는 계정 동기화 기능을 제공하지 않습니다."\n            )': '            .setMessage(R.string.location_disclosure_body)',
    '.setNegativeButton("취소", null)': '.setNegativeButton(R.string.cancel, null)',
    '.setPositiveButton("동의하고 시작")': '.setPositiveButton(R.string.agree_start)',
    'trackingStatusText.text = "● 탐험 시작 요청됨 · GPS 연결 확인 중"': 'trackingStatusText.text = getString(R.string.tracking_requested)',
    'countText.text = "탐험을 시작하지 못했습니다. 위치 권한과 기기 설정을 확인하세요."': 'countText.text = getString(R.string.tracking_failed)',
    '.setTitle("정확한 위치 권한이 필요합니다")': '.setTitle(R.string.permission_required_title)',
    '.setMessage("약 10m 범위의 탐험 지도를 만들려면 정확한 위치 권한이 필요합니다. 설정에서 위치 권한을 \'정확한 위치\'로 허용한 뒤 다시 시작해 주세요.")': '.setMessage(R.string.permission_required_body)',
    '.setPositiveButton("앱 설정 열기")': '.setPositiveButton(R.string.open_app_settings)',
    '.setNegativeButton("닫기", null)': '.setNegativeButton(R.string.close, null)',
    'countText.text = "지도 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."': 'countText.text = getString(R.string.map_load_failed)',
    'trackingStatusText.text = if (running) "● 자동 탐험 중 · GPS 위치 수신/기록 중" else "● 탐험 중지됨"': 'trackingStatusText.text = getString(if (running) R.string.tracking_active else R.string.tracking_inactive)',
    'android.widget.Toast.makeText(this, "현재 위치를 확인하지 못했습니다. 자동 탐험을 시작해 주세요.", android.widget.Toast.LENGTH_SHORT).show()': 'android.widget.Toast.makeText(this, R.string.current_location_unavailable, android.widget.Toast.LENGTH_SHORT).show()',
}
for old, new in replacements.items():
    if old not in s:
        raise SystemExit(f"MainActivity localization target not found: {old[:100]}")
    s = s.replace(old, new, 1)

old_summary = 'countText.text = "🌍 지구 탐험률\\n$percentLabel\\n공개 면적 $areaLabel"'
summary_count = s.count(old_summary)
if summary_count != 1:
    raise SystemExit(f"Expected one exploration summary to localize, found {summary_count}")
s = s.replace(old_summary, 'countText.text = getString(R.string.exploration_summary, percentLabel, areaLabel)')

# Add a language control next to the location permission control.
old = '''        val settings = Button(this).apply { text = getString(R.string.location_permission_settings); setOnClickListener { openAppSettings() } }
        row2.addView(settings, LinearLayout.LayoutParams(-1, -2, 1f))
'''
new = '''        val settings = Button(this).apply { text = getString(R.string.location_permission_settings); setOnClickListener { openAppSettings() } }
        val language = Button(this).apply {
            text = getString(R.string.language)
            setOnClickListener { showLanguageDialog() }
        }
        row2.addView(settings, LinearLayout.LayoutParams(0, -2, 1f))
        row2.addView(language, LinearLayout.LayoutParams(0, -2, 1f))
'''
assert old in s
s = s.replace(old, new, 1)

# Nickname dialog strings are introduced by the preceding v0.7.9 patch.
s = s.replace('contentDescription = "탐험가 닉네임 설정"', 'contentDescription = getString(R.string.nickname_accessibility)')
s = s.replace('if (nickname.isBlank()) "🌍  지구 탐험 · 닉네임 설정" else "🌍  지구 탐험 · $nickname"',
              'if (nickname.isBlank()) getString(R.string.nickname_header_empty) else getString(R.string.nickname_header, nickname)')
s = s.replace('hint = "2~12자 · 한글, 영문, 숫자, 밑줄"', 'hint = getString(R.string.nickname_hint)')
s = s.replace('if (required) "탐험가 닉네임 만들기" else "닉네임 변경"',
              'getString(if (required) R.string.nickname_create_title else R.string.nickname_change_title)')
s = s.replace('.setMessage("지도와 향후 세계 탐험 랭킹에 표시할 이름입니다. 닉네임은 2~12자로 입력해 주세요.")',
              '.setMessage(R.string.nickname_message)')
s = s.replace('.setPositiveButton("저장", null)', '.setPositiveButton(R.string.save, null)')
s = s.replace('input.error = "2~12자 한글·영문·숫자·밑줄만 사용할 수 있습니다."', 'input.error = getString(R.string.nickname_invalid)')
activity.write_text(s, encoding="utf-8")

# Add persistent language selection. Recreate only the Activity; SQLite and tracking service remain untouched.
needle = '    private fun requestAndStart() {'
method = '''    private fun showLanguageDialog() {
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
assert needle in s
s = s.replace(needle, method + needle, 1)
activity.write_text(s, encoding="utf-8")

privacy = new_dir / "PrivacyPolicyActivity.kt"
p = privacy.read_text(encoding="utf-8")
p = p.replace('text = "지구 탐험 개인정보 처리 안내"', 'text = getString(R.string.privacy_title)')
p = p.replace('text = POLICY_TEXT', 'text = getString(R.string.privacy_body)')
p = p.replace('text = "닫기"', 'text = getString(R.string.close)')
privacy.write_text(p, encoding="utf-8")

# The foreground-service notification must use the same app-language preference.
service = new_dir / "LocationTrackingService.kt"
svc = service.read_text(encoding="utf-8")
svc = svc.replace("import android.content.Intent\\n", "import android.content.Context\\nimport android.content.Intent\\n", 1)
service_attach = "    override fun onCreate() {"
assert service_attach in svc
svc = svc.replace(service_attach, """    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

"""+service_attach, 1)
for old, new in {
    '"지구 탐험 위치 기록"':'getString(R.string.tracking_channel_name)',
    'setContentTitle("지구 탐험 기록 중")':'setContentTitle(getString(R.string.tracking_notification_title))',
    'setContentText("이동 경로 주변을 자동으로 탐험하고 있습니다.")':'setContentText(getString(R.string.tracking_notification_text))',
    'Notification.Action.Builder(null, "탐험 중지", stop)':'Notification.Action.Builder(null, getString(R.string.tracking_notification_stop), stop)',
}.items():
    if old not in svc:
        raise SystemExit(f"Service localization target not found: {old}")
    svc = svc.replace(old, new, 1)
service.write_text(svc, encoding="utf-8")


# Expose supported languages to Android 13+ system app-language settings.
xml_dir = res / "xml"
xml_dir.mkdir(parents=True, exist_ok=True)
(xml_dir / "locales_config.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<locale-config xmlns:android="http://schemas.android.com/apk/res/android">
    <locale android:name="en" />
    <locale android:name="ko" />
</locale-config>
''', encoding="utf-8")
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:label="@string/app_name"', 'android:label="@string/app_name"\n        android:localeConfig="@xml/locales_config"')
manifest.write_text(m, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 34', 'versionCode = 35')
v = v.replace('versionName = "0.8.0"', 'versionName = "0.8.1"')
v += '''
# Permanent package ID and initial Korean/English localization must be present.
grep -F 'applicationId = "com.earthunlock.app"' app/build.gradle.kts >/dev/null
grep -F 'namespace = "com.earthunlock.app"' app/build.gradle.kts >/dev/null
grep -F 'android:localeConfig="@xml/locales_config"' app/src/main/AndroidManifest.xml >/dev/null
grep -F 'name="language_dialog_title"' app/src/main/res/values/strings.xml >/dev/null
grep -F 'name="language_dialog_title"' app/src/main/res/values-ko/strings.xml >/dev/null
grep -F 'AppLocale.wrap(newBase)' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'putString("app_language", values[which])' app/src/main/java/com/earthunlock/app/MainActivity.kt >/dev/null
grep -F 'AppLocale.wrap(newBase)' app/src/main/java/com/earthunlock/app/LocationTrackingService.kt >/dev/null
grep -F 'tracking_notification_title' app/src/main/res/values/strings.xml >/dev/null
'''
verify.write_text(v, encoding="utf-8")

# Package and localization unit tests.
test_dir = root / "app/src/test/java/com/earthunlock/app"
test_dir.mkdir(parents=True, exist_ok=True)
(test_dir / "AppLocaleTest.kt").write_text('''package com.earthunlock.app

import org.junit.Assert.assertEquals
import org.junit.Test

class AppLocaleTest {
    @Test fun supportedLanguageTagsAreStable() {
        assertEquals("system", AppLocale.SYSTEM)
        assertEquals("ko", AppLocale.KOREAN)
        assertEquals("en", AppLocale.ENGLISH)
    }
}
''', encoding="utf-8")

print("EARTH UNLOCK v0.8.1 permanent package ID and Korean/English localization patch applied")
