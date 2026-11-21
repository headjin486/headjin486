from pathlib import Path
import sys

root = Path(sys.argv[1])
pkg = root / "app/src/main/java/com/earthunlock/app"
activity = pkg / "MainActivity.kt"
a = activity.read_text(encoding="utf-8")

imports = [
    "import android.widget.Toast",
    "import com.google.android.gms.auth.api.signin.GoogleSignIn",
    "import com.google.android.gms.auth.api.signin.GoogleSignInOptions",
    "import com.google.android.gms.common.api.ApiException",
    "import com.google.firebase.auth.FirebaseAuth",
    "import com.google.firebase.auth.GoogleAuthProvider",
]
for line in imports:
    if line not in a:
        a = a.replace("import android.widget.TextView\n", "import android.widget.TextView\n" + line + "\n", 1)

ui_anchor = "        panel.addView(cloudBackupButton, LinearLayout.LayoutParams(-1, -2))"
if "MY_EARTH_GOOGLE_RECOVERY_BUTTON" not in a:
    if ui_anchor not in a:
        raise SystemExit("Cloud backup button anchor missing")
    ui = r'''
        // MY_EARTH_GOOGLE_RECOVERY_BUTTON: link this device or restore an existing Google-linked UID.
        val googleRecoveryButton = Button(this).apply {
            text = "Google 계정 연결 / 기기 변경 복원"
            isAllCaps = false
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Google 계정으로 기록 보호")
                    .setMessage("현재 휴대폰에서는 익명 계정을 Google 계정에 연결해 기기 변경에 대비할 수 있습니다. 새 휴대폰에서는 기존 Google 계정으로 로그인해 클라우드 기록을 현재 기록과 병합할 수 있습니다.")
                    .setPositiveButton("현재 기록을 Google에 연결") { _, _ ->
                        startGoogleRecoveryFlow(restoreExisting = false)
                    }
                    .setNeutralButton("기존 Google 계정으로 복원") { _, _ ->
                        startGoogleRecoveryFlow(restoreExisting = true)
                    }
                    .setNegativeButton("취소", null)
                    .show()
            }
        }
        panel.addView(googleRecoveryButton, LinearLayout.LayoutParams(-1, -2))
'''
    a = a.replace(ui_anchor, ui_anchor + "\n" + ui, 1)

method_anchor = "    private fun requestAndStart() {"
if "private fun startGoogleRecoveryFlow" not in a:
    if method_anchor not in a:
        raise SystemExit("MainActivity requestAndStart insertion point missing")
    methods = r'''
    private fun startGoogleRecoveryFlow(restoreExisting: Boolean) {
        val webClientId = resources.getIdentifier("default_web_client_id", "string", packageName)
        if (webClientId == 0) {
            Toast.makeText(this, "Firebase 설정에 Google 로그인 정보가 없습니다. Google 로그인 사용 설정 후 google-services.json을 갱신해야 합니다.", Toast.LENGTH_LONG).show()
            return
        }
        val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(getString(webClientId))
            .requestEmail()
            .build()
        val client = GoogleSignIn.getClient(this, options)
        startActivityForResult(client.signInIntent, if (restoreExisting) 9205 else 9204)
    }

    @Deprecated("Google Sign-In activity result bridge")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != 9204 && requestCode != 9205) return
        if (resultCode != RESULT_OK || data == null) {
            Toast.makeText(this, "Google 로그인이 취소되었습니다.", Toast.LENGTH_SHORT).show()
            return
        }
        try {
            val account = GoogleSignIn.getSignedInAccountFromIntent(data)
                .getResult(ApiException::class.java)
            val token = account.idToken
            if (token.isNullOrBlank()) {
                Toast.makeText(this, "Google 인증 토큰을 받지 못했습니다. Firebase Google 로그인 설정을 확인하세요.", Toast.LENGTH_LONG).show()
                return
            }
            val credential = GoogleAuthProvider.getCredential(token, null)
            val auth = FirebaseAuth.getInstance()

            if (requestCode == 9205) {
                // Explicit restore action: authenticate the chosen Google account, then merge
                // this device's local cells with that account's cloud cells.
                auth.signOut()
                auth.signInWithCredential(credential)
                    .addOnSuccessListener {
                        FirebaseBackupManager.setEnabled(this, true)
                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                        Toast.makeText(this, "Google 계정 연결 완료. 기존 기록을 복원하고 있습니다.", Toast.LENGTH_LONG).show()
                    }
                    .addOnFailureListener { error ->
                        Toast.makeText(this, "기록 복원 로그인 실패: \${error.localizedMessage}", Toast.LENGTH_LONG).show()
                    }
            } else {
                val current = auth.currentUser
                if (current?.providerData?.any { it.providerId == "google.com" } == true) {
                    FirebaseBackupManager.setEnabled(this, true)
                    FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                    Toast.makeText(this, "이미 Google 계정이 연결되어 있습니다.", Toast.LENGTH_SHORT).show()
                } else if (current != null) {
                    current.linkWithCredential(credential)
                        .addOnSuccessListener {
                            FirebaseBackupManager.setEnabled(this, true)
                            FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                            Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                        }
                        .addOnFailureListener { error ->
                            Toast.makeText(this, "계정 연결 실패: \${error.localizedMessage}. 이미 사용 중인 Google 계정이라면 '기존 Google 계정으로 복원'을 선택하세요.", Toast.LENGTH_LONG).show()
                        }
                } else {
                    auth.signInAnonymously()
                        .addOnSuccessListener { result ->
                            val anonymousUser = result.user
                            if (anonymousUser == null) {
                                Toast.makeText(this, "익명 계정을 준비하지 못했습니다.", Toast.LENGTH_LONG).show()
                            } else {
                                anonymousUser.linkWithCredential(credential)
                                    .addOnSuccessListener {
                                        FirebaseBackupManager.setEnabled(this, true)
                                        FirebaseBackupManager.requestSyncIfEnabled(this, store, true)
                                        Toast.makeText(this, "현재 탐험 기록을 Google 계정에 연결했습니다.", Toast.LENGTH_LONG).show()
                                    }
                                    .addOnFailureListener { error ->
                                        Toast.makeText(this, "계정 연결 실패: \${error.localizedMessage}", Toast.LENGTH_LONG).show()
                                    }
                            }
                        }
                        .addOnFailureListener { error ->
                            Toast.makeText(this, "익명 계정 생성 실패: \${error.localizedMessage}", Toast.LENGTH_LONG).show()
                        }
                }
            }
        } catch (error: ApiException) {
            Toast.makeText(this, "Google 로그인 오류: \${error.statusCode}", Toast.LENGTH_LONG).show()
        } catch (error: Exception) {
            Toast.makeText(this, "로그인 처리 오류: \${error.localizedMessage}", Toast.LENGTH_LONG).show()
        }
    }

'''
    a = a.replace(method_anchor, methods + method_anchor, 1)

activity.write_text(a, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'play-services-auth' not in g:
    g = g.replace('dependencies {', '''dependencies {
    implementation("com.google.android.gms:play-services-auth:21.3.0")''', 1)
if 'versionCode = 66' not in g or 'versionName = "0.10.13"' not in g:
    raise SystemExit("Unexpected app version; refusing to overwrite version metadata")
g = g.replace('versionCode = 66', 'versionCode = 67', 1).replace('versionName = "0.10.13"', 'versionName = "0.10.14"', 1)
gradle.write_text(g, encoding="utf-8")

manager = pkg / "FirebaseBackupManager.kt"
m = manager.read_text(encoding="utf-8")
if "fun deleteCloudBackup" not in m:
    anchor = "    private fun encode(cells: List<Pair<Long, Long>>): String {"
    if anchor not in m:
        raise SystemExit("Firebase backup encode insertion point missing")
    delete_method = r'''
    /** Delete only this user's cloud backup documents; local SQLite data is untouched. */
    fun deleteCloudBackup(onComplete: (Boolean) -> Unit) {
        val uid = FirebaseAuth.getInstance().currentUser?.uid
        if (uid.isNullOrBlank()) {
            onComplete(true)
            return
        }
        val chunks = FirebaseFirestore.getInstance()
            .collection("exploration_backups").document(uid).collection("chunks")
        chunks.get()
            .addOnSuccessListener { snapshot ->
                if (snapshot.isEmpty) {
                    onComplete(true)
                } else {
                    val tasks = snapshot.documents.chunked(400).map { documents ->
                        val batch = FirebaseFirestore.getInstance().batch()
                        documents.forEach { batch.delete(it.reference) }
                        batch.commit()
                    }
                    com.google.android.gms.tasks.Tasks.whenAll(tasks)
                        .addOnCompleteListener { onComplete(it.isSuccessful) }
                }
            }
            .addOnFailureListener { onComplete(false) }
    }

'''
    m = m.replace(anchor, delete_method + anchor, 1)
manager.write_text(m, encoding="utf-8")

# Add cloud data deletion to the existing backup dialog.
if "클라우드 백업 데이터 삭제" not in a:
    a = a.replace(
        '.setNegativeButton("백업 끄기") { _, _ ->\n                            FirebaseBackupManager.setEnabled(this@MainActivity, false)\n                            text = "☁  클라우드 백업 설정"\n                        }',
        '.setNegativeButton("백업 끄기") { _, _ ->\n                            FirebaseBackupManager.setEnabled(this@MainActivity, false)\n                            text = "☁  클라우드 백업 설정"\n                        }\n                        .setNeutralButton("클라우드 백업 데이터 삭제") { _, _ ->\n                            AlertDialog.Builder(this@MainActivity)\n                                .setTitle("클라우드 백업 삭제")\n                                .setMessage("서버에 저장된 해금 지도 셀 백업을 삭제합니다. 휴대폰 내부의 GPS 기록과 지도 데이터는 삭제되지 않습니다.")\n                                .setNegativeButton("취소", null)\n                                .setPositiveButton("삭제") { _, _ ->\n                                    FirebaseBackupManager.setEnabled(this@MainActivity, false)\n                                    FirebaseBackupManager.deleteCloudBackup { success ->\n                                        Toast.makeText(this@MainActivity, if (success) "클라우드 백업 데이터를 삭제했습니다." else "삭제하지 못했습니다. 네트워크 연결 후 다시 시도하세요.", Toast.LENGTH_LONG).show()\n                                        text = "☁  클라우드 백업 설정"\n                                    }\n                                }\n                                .show()\n                        }'
    )
    activity.write_text(a, encoding="utf-8")

policy = pkg / "PrivacyPolicyActivity.kt"
p = policy.read_text(encoding="utf-8")
old = "GPS 기록과 탐험 격자는 기본적으로 Android 기기 내부의 앱 전용 SQLite 데이터베이스에 저장됩니다. 현재 버전은 계정 기반 서버 동기화 기능을 제공하지 않습니다. 앱 데이터 삭제 또는 앱 제거 시 로컬 기록이 삭제됩니다. 앱 자동 백업은 비활성화되어 있습니다."
new = "GPS 좌표, 위치 정확도, 측정 시각 및 상세 이동 기록은 Android 기기 내부의 앱 전용 SQLite 데이터베이스에 저장됩니다. 사용자가 클라우드 백업에 명시적으로 동의한 경우에만 해금된 5m 지도 셀 식별자와 Firebase 익명 사용자 식별자를 Firebase Cloud Firestore(서울 리전 asia-northeast3)에 전송합니다. 원본 GPS 좌표, 시간순 이동 경로 및 GPS 측정 시각은 클라우드로 전송하지 않습니다. 백업은 사용자가 끌 때까지 동작하며, 이미 저장된 클라우드 백업은 앱의 클라우드 백업 데이터 삭제 기능으로 별도 삭제할 수 있습니다. 앱 자동 백업은 비활성화되어 있습니다."
if old in p:
    p = p.replace(old, new, 1)
elif new not in p:
    raise SystemExit("Privacy policy cloud-backup insertion text not found")
p = p.replace("기록은 앱 전용 내부 저장소에 보관하며 Android 자동 백업을 비활성화했습니다.", "GPS 원본 기록은 앱 전용 내부 저장소에 보관합니다. 클라우드 백업에 동의한 경우 해금 셀 식별자만 Firebase에 전송하며, 이용자는 앱에서 이후 백업을 중지하거나 기존 클라우드 백업 데이터를 삭제할 수 있습니다. 기기 자체의 보안 위험까지 완전히 방지할 수는 없습니다.", 1)
policy.write_text(p, encoding="utf-8")

print("Added Google account linking/restoration, cloud backup deletion, and privacy notice updates.")
