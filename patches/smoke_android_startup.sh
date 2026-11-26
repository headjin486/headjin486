#!/usr/bin/env bash
# Real Android 16 startup gate for signed release builds; no real user data.
set -euo pipefail
PKG=com.earthunlock.app
ACT="$PKG/.MainActivity"
API_IMAGE='system-images;android-36;google_apis;x86_64'
AVD=my_earth_startup
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:?Android SDK not available}}"
export PATH="$SDK/emulator:$SDK/platform-tools:$PATH"
sudo chmod a+rw /dev/kvm
sdkmanager --install "emulator" "$API_IMAGE"
echo no | avdmanager create avd --force -n "$AVD" -k "$API_IMAGE"
emulator -avd "$AVD" -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader_indirect > /tmp/my-earth-emulator.log 2>&1 &
EMULATOR_PID=$!
trap 'adb emu kill >/dev/null 2>&1 || true; kill "$EMULATOR_PID" >/dev/null 2>&1 || true' EXIT
timeout 240 adb wait-for-device
for n in $(seq 1 100); do
  if [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == "1" ]]; then break; fi
  sleep 3
done
[[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == "1" ]] || { tail -80 /tmp/my-earth-emulator.log; exit 1; }
adb shell input keyevent 82
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

launch_check() {
  local label="$1"
  adb shell am force-stop "$PKG"
  adb logcat -b crash -c
  adb shell am start -W -n "$ACT"
  sleep 8
  adb logcat -b crash -d > "/tmp/my-earth-$label-crash.txt"
  if grep -F "Process: $PKG" "/tmp/my-earth-$label-crash.txt"; then
    cat "/tmp/my-earth-$label-crash.txt"
    echo "FAILED: $label crashed"
    return 1
  fi
  adb shell pidof "$PKG" || { echo "FAILED: $label not running"; return 1; }
  adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' | grep -F "$PKG" || { echo "FAILED: $label not resumed"; return 1; }
  echo "PASS: $label launched and remains visible"
}

# Reproduce the released 0.10.46 failure when possible, then test an in-place update.
adb install previous-1046/app-release.apk
if launch_check old-1046; then
  echo "Previous failure not reproduced on API 36; regression gate still tests both install paths."
else
  echo "Previous release startup failure reproduced on emulator."
fi
adb install -r source/app/build/outputs/apk/release/app-release.apk
launch_check upgrade-1047
# Force-stop/relaunch also checks lifecycle and handler initialization.
launch_check relaunch-1047
# Emulator-only uninstall; tests the fresh-install path without touching user devices.
adb uninstall "$PKG"
adb install source/app/build/outputs/apk/release/app-release.apk
launch_check fresh-1047
echo "All 0.10.47 startup checks passed."
