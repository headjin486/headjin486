from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

# The prominent disclosure must be shown before the Android runtime permission prompt.
start = a.find("    private fun requestAndStart() {")
end = a.find("    private fun openAppSettings() {", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate location permission flow; refusing unsafe rewrite")

replacement = r'''    private fun requestAndStart() {
        val preferences = getSharedPreferences("my_earth_privacy", MODE_PRIVATE)
        if (preferences.getBoolean("location_disclosure_accepted_v1", false)) {
            requestLocationPermissionOrStart()
        } else {
            showLocationDisclosureAndStart()
        }
    }

    private fun showLocationDisclosureAndStart() {
        AlertDialog.Builder(this)
            .setTitle("위치 정보 수집 및 이용 안내")
            .setMessage(
                "이 앱은 앱이 닫혀 있거나 사용 중이 아닐 때에도 자동 탐험, 현재 위치 표시, " +
                    "이동 경로 주변 지도 해금 기능을 제공하기 위해 위치 데이터를 수집합니다.\n\n" +
                    "자동 탐험을 시작하면 GPS 위도·경도, 위치 정확도, 측정 시각을 처리하여 " +
                    "현재 위치를 표시하고 지나간 주변의 지도 영역을 해금합니다. " +
                    "탐험은 사용자가 직접 시작하며, 다른 앱을 사용하거나 화면이 꺼진 뒤에도 " +
                    "사용자가 탐험을 중지할 때까지 Android 포그라운드 서비스로 위치 기록이 계속됩니다. " +
                    "상태 알림이 표시됩니다.\n\n" +
                    "원본 GPS 좌표와 시간순 이동 경로는 이 기기 안에 저장됩니다. " +
                    "별도로 클라우드 백업에 동의한 경우에만 해금된 5m 지도 셀 식별자를 Firebase에 저장하며, " +
                    "원본 GPS 좌표와 이동 경로는 클라우드에 전송하지 않습니다. " +
                    "지도 표시를 위해 지도 타일 제공자에 지도 영역 요청이 전송될 수 있습니다.\n\n" +
                    "동의하지 않으면 위치 권한을 요청하거나 자동 탐험을 시작하지 않습니다."
            )
            .setNegativeButton("취소", null)
            .setPositiveButton("내용을 확인했고 동의합니다") { _, _ ->
                getSharedPreferences("my_earth_privacy", MODE_PRIVATE)
                    .edit().putBoolean("location_disclosure_accepted_v1", true).apply()
                requestLocationPermissionOrStart()
            }
            .show()
    }

    private fun requestLocationPermissionOrStart() {
        val fineGranted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        if (fineGranted) {
            startLocationTrackingService()
            return
        }
        val permissions = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        ActivityCompat.requestPermissions(this, permissions, requestCode)
    }

    private fun startLocationTrackingService() {
        try {
            ContextCompat.startForegroundService(
                this,
                Intent(this, LocationTrackingService::class.java)
            )
            trackingStatusText.text = "● 탐험 시작 요청됨 · GPS 연결 확인 중"
            refreshTrackingStatus()
        } catch (e: Exception) {
            countText.text = "탐험을 시작하지 못했습니다. 위치 권한과 기기 설정을 확인하세요."
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != this.requestCode) return
        val fineGranted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        if (fineGranted) {
            startLocationTrackingService()
        } else {
            AlertDialog.Builder(this)
                .setTitle("정확한 위치 권한이 필요합니다")
                .setMessage("약 12m 범위의 탐험 지도를 만들려면 정확한 위치 권한이 필요합니다. 설정에서 정확한 위치 권한을 허용한 뒤 다시 시작해 주세요.")
                .setPositiveButton("앱 설정 열기") { _, _ -> openAppSettings() }
                .setNegativeButton("닫기", null)
                .show()
        }
    }

'''
a = a[:start] + replacement + a[end:]
if a.find("위치 정보 수집 및 이용 안내") > a.find("ActivityCompat.requestPermissions(this, permissions, requestCode)"):
    raise SystemExit("Disclosure ordering check failed")
activity.write_text(a, encoding="utf-8")

# Replace the stale privacy notice with the actual opt-in Firebase backup design.
policy = pkg / "PrivacyPolicyActivity.kt"
p = policy.read_text(encoding="utf-8")
policy_text = r'''        private val POLICY_TEXT = """
시행일: 2026-11-22
운영자 및 개인정보 문의: MY EARTH 운영자 · headjin486@gmail.com

1. 처리하는 정보
자동 탐험을 사용자가 직접 시작하고 위치 이용 안내에 동의한 동안 GPS 위도·경도, 위치 정확도, 측정 시각을 처리합니다. 현재 위치 표시, 지나간 지도 영역 해금, 이동 기록 및 탐험 통계 계산에 사용합니다. 사용자가 Google 계정을 연결하면 Firebase Authentication이 계정 식별 정보(예: UID 및 Google 계정 이메일)를 처리할 수 있습니다.

2. 처리 목적 및 위치 기록 방식
자동 탐험은 사용자가 앱에서 직접 시작합니다. 앱이 다른 화면에 있거나 화면이 꺼진 동안에도 사용자가 중지할 때까지 Android 포그라운드 서비스가 위치를 기록합니다. 상시 백그라운드 추적이나 광고·분석 목적의 위치 수집은 하지 않습니다. 이용자는 앱의 탐험 중지 버튼 또는 시스템 알림의 중지 동작으로 기록을 중단할 수 있습니다.

3. 저장 위치 및 보유 기간
원본 GPS 좌표, 위치 정확도, 측정 시각 및 시간순 이동 경로는 기기 내부 앱 전용 SQLite 데이터베이스에 저장되며, 앱 데이터 삭제 또는 앱 제거 시 삭제됩니다. Android 자동 백업은 비활성화되어 있습니다.
클라우드 백업은 이용자가 Google 계정을 연결하고 별도 동의한 경우에만 활성화됩니다. 이때 백업되는 정보는 해금된 5m 지도 격자의 식별자(cell_x, cell_y)뿐입니다. 원본 GPS 좌표, 시간순 이동 경로, GPS 측정 시각은 클라우드로 전송하지 않습니다. 백업 정보는 Firebase Cloud Firestore 서울 리전(asia-northeast3)에 계정 UID별로 저장되며, 이용자가 클라우드 백업 데이터를 삭제할 때까지 보유합니다. 백업을 끄는 것만으로 이미 저장된 백업이 자동 삭제되지는 않으므로, 기존 백업 삭제 기능을 별도로 이용해야 합니다.

4. 외부 서비스 및 제공받는 자
- Google Firebase Authentication: 익명 사용자 인증 및 이용자가 선택한 Google 계정 연결 처리.
- Google Firebase Cloud Firestore: 이용자가 별도 동의한 경우 해금 지도 셀 식별자 백업 저장.
- OpenStreetMap 기반 지도 타일 제공자: 지도 표시를 위한 타일 요청. 요청 과정에서 IP 주소, 요청한 지도 영역, 접속 시각 등 네트워크 정보가 처리될 수 있습니다. 앱은 GPS 좌표나 시간순 이동 경로를 지도 타일 제공자에게 별도로 전송하지 않습니다.
현재 배포 준비 버전에는 광고 SDK 및 분석 SDK가 포함되어 있지 않습니다.

5. 이용자의 선택과 통제
정확한 위치 권한을 허용하지 않으면 자동 탐험 기능을 사용할 수 없습니다. 위치 권한은 Android 설정에서 철회할 수 있습니다. 클라우드 백업은 이용자가 별도로 동의해야 켜지며, 앱에서 백업을 끄거나 이미 저장된 클라우드 백업 데이터를 삭제할 수 있습니다. 클라우드 백업 삭제는 기기 내부의 GPS 기록과 지도 데이터를 삭제하지 않습니다.

6. 보안 및 문의
Firebase 접근은 인증된 사용자별 Firestore 보안 규칙으로 제한합니다. 기기 내부 기록은 앱 전용 저장소에 보관합니다. 네트워크·기기 보안 위험을 완전히 방지할 수는 없습니다. 개인정보 관련 문의는 위 운영자 연락처로 접수할 수 있습니다.

[출시 전 필수] 운영자명과 공개 문의 이메일을 실제 정보로 교체하고, 실제 앱 동작 및 외부 서비스 약관을 검토한 뒤 공개 개인정보 처리방침 URL을 게시해야 합니다. 계정 전체 삭제 절차와 외부 웹 삭제 요청 경로가 완성되기 전에는 Google Play 출시를 진행하지 않습니다.
""".trimIndent()'''
pattern = re.compile(r'        private (?:const )?val POLICY_TEXT = """[\s\S]*?""".trimIndent\(\)')
p2, n = pattern.subn(policy_text, p, count=1)
if n != 1:
    raise SystemExit("Could not safely replace existing privacy policy text")
policy.write_text(p2, encoding="utf-8")

# Bump app version without changing package ID, local database, or signing configuration.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 78' not in g or 'versionName = "0.10.25"' not in g:
    raise SystemExit("Unexpected app version; expected v0.10.25")
g = g.replace('versionCode = 78', 'versionCode = 79', 1)
g = g.replace('versionName = "0.10.25"', 'versionName = "0.10.26"', 1)
gradle.write_text(g, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v += '''
# v0.10.26: prominent location disclosure must precede runtime permission request.
python - <<'PY'
from pathlib import Path
s = Path("app/src/main/java/com/earthunlock/app/MainActivity.kt").read_text(encoding="utf-8")
disclosure = s.index("private fun showLocationDisclosureAndStart()")
permission = s.index("ActivityCompat.requestPermissions(this, permissions, requestCode)")
assert disclosure < permission
assert "location_disclosure_accepted_v1" in s
assert "앱이 닫혀 있거나 사용 중이 아닐 때에도" in s
assert "원본 GPS 좌표와 이동 경로는 클라우드에 전송하지 않습니다" in s
p = Path("app/src/main/java/com/earthunlock/app/PrivacyPolicyActivity.kt").read_text(encoding="utf-8")
assert "asia-northeast3" in p and "원본 GPS 좌표" in p
PY
grep -F 'versionCode = 79' app/build.gradle.kts >/dev/null
grep -F 'versionName = "0.10.26"' app/build.gradle.kts >/dev/null
'''
v = v.replace("versionCode = 78", "versionCode = 79")
v = v.replace('versionName = "0.10.25"', 'versionName = "0.10.26"')
verify.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.26: moved prominent location disclosure ahead of Android permission request and updated privacy disclosure for opt-in Firebase cell backup.")
