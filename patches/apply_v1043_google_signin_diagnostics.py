from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = root / "app/src/main/java/com/earthunlock/app/MainActivity.kt"
s = activity.read_text(encoding="utf-8")

old = '''        if (resultCode != RESULT_OK || data == null) {
            Toast.makeText(this, "Google 로그인이 취소되었습니다.", Toast.LENGTH_SHORT).show()
            return
        }'''
new = '''        if (resultCode != RESULT_OK || data == null) {
            val detail = if (data != null) {
                try {
                    GoogleSignIn.getSignedInAccountFromIntent(data)
                        .getResult(ApiException::class.java)
                    "resultCode=$resultCode, accountResult=present"
                } catch (error: ApiException) {
                    "resultCode=$resultCode, statusCode=${error.statusCode}, message=${error.message ?: "없음"}"
                } catch (error: Exception) {
                    "resultCode=$resultCode, error=${error.javaClass.simpleName}: ${error.message ?: "없음"}"
                }
            } else {
                "resultCode=$resultCode, data=null"
            }
            Toast.makeText(this, "Google 로그인 실패: $detail", Toast.LENGTH_LONG).show()
            return
        }'''
if old not in s:
    raise SystemExit("Expected Google Sign-In cancellation block not found; refusing patch")
s = s.replace(old, new, 1)
s = s.replace('Google 로그인 오류: \\${error.statusCode}', 'Google 로그인 오류: ${error.statusCode}')
activity.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'versionCode = 95' not in g or 'versionName = "0.10.42"' not in g:
    raise SystemExit("Expected v0.10.42 base version; refusing unsafe version bump")
g = g.replace('versionCode = 95', 'versionCode = 96', 1)
g = g.replace('versionName = "0.10.42"', 'versionName = "0.10.43"', 1)
gradle.write_text(g, encoding="utf-8")

verifier = root / "scripts/verify-play-release-policy.py"
v = verifier.read_text(encoding="utf-8")
if 'versionCode = 95' not in v or 'versionName = "0.10.42"' not in v:
    raise SystemExit("Expected v0.10.42 release verifier; refusing unsafe version bump")
v = v.replace('versionCode = 95', 'versionCode = 96', 1)
v = v.replace('versionName = "0.10.42"', 'versionName = "0.10.43"', 1)
verifier.write_text(v, encoding="utf-8")

print("MY EARTH v0.10.43: expose Google Sign-In failure status for diagnosis.")
