from pathlib import Path
import sys

root = Path(sys.argv[1])
build = root / "app/build.gradle.kts"
s = build.read_text(encoding="utf-8")

assert 'versionCode = 31' in s and 'versionName = "0.7.7"' in s
s = s.replace('versionCode = 31', 'versionCode = 32', 1)
s = s.replace('versionName = "0.7.7"', 'versionName = "0.7.8"', 1)

needle = '    buildTypes {\n'
insert = '''    buildTypes {
      // Use the persistent upload key for locally distributed debug builds too.
      // This allows the next test APK to update the prior build without uninstalling.
      getByName("debug") {
        if (hasReleaseSigning) signingConfig = signingConfigs.getByName("release")
      }
'''
assert s.count(needle) == 1
s = s.replace(needle, insert, 1)
build.write_text(s, encoding="utf-8")

verify = root / "scripts/verify-service-lifecycle.sh"
v = verify.read_text(encoding="utf-8")
v = v.replace('versionCode = 31', 'versionCode = 32')
v = v.replace('versionName = "0.7.7"', 'versionName = "0.7.8"')
if "Persistent debug signing must be configured" not in v:
    v += '''
# Persistent signing must be wired to debug builds for safe iterative installs.
grep -F 'getByName("debug")' app/build.gradle.kts >/dev/null
grep -F 'signingConfig = signingConfigs.getByName("release")' app/build.gradle.kts >/dev/null
'''
verify.write_text(v, encoding="utf-8")
