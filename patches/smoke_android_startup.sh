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
printf 'no\n' | avdmanager create avd --force -n "$AVD" -k "$API_IMAGE" --device pixel_6
emulator -accel-check
emulator -list-avds
adb start-server
# Print startup diagnostics even when adb can't see the emulator.
LOG=/tmp/my-earth-emulator.log
emulator -avd "$AVD" -port 5554 -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader -memory 2048 -camera-back none -camera-front none -verbose </dev/null >"$LOG" 2>&1 &
EMULATOR_PID=$!
cleanup() {
  result=$?
  if [[ "$result" -ne 0 ]]; then
    echo "Emulator / startup gate failed (exit $result)"
    tail -100 "$LOG" || true
    adb devices -l || true
    df -h || true
  fi
  adb emu kill >/dev/null 2>&1 || true
  kill "$EMULATOR_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT
for n in $(seq 1 90); do
  kill -0 "$EMULATOR_PID" 2>/dev/null || { echo "Emulator exited during boot"; exit 1; }
  if [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)" == "1" ]]; then break; fi
  sleep 3
done
[[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)" == "1" ]] || { echo "Emulator did not boot"; exit 1; }
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
if [[ -f previous-1046/app-release.apk ]]; then
  adb install previous-1046/app-release.apk
  if launch_check old-1046; then
    echo "Previous failure not reproduced on API 36; regression gate still tests both install paths."
  else
    echo "Previous release startup failure reproduced on emulator."
  fi
else
  adb install source/app/build/outputs/apk/release/app-release.apk
  launch_check initial-1047
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
