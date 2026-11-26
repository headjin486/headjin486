#!/usr/bin/env bash
# Real Android 16 startup gate for signed release builds; no real user data.
set -euo pipefail
PKG=com.earthunlock.app
ACT="$PKG/.MainActivity"
API_IMAGE='system-images;android-36;google_apis;x86_64'
AVD=my_earth_startup
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:?Android SDK not available}}"
export PATH="$SDK/emulator:$SDK/platform-tools:$PATH"
# Use one explicit AVD directory for both SDK manager and emulator.
export ANDROID_AVD_HOME="${RUNNER_TEMP:-/tmp}/my-earth-avds"
mkdir -p "$ANDROID_AVD_HOME"

sudo chmod a+rw /dev/kvm
sdkmanager --install "emulator" "$API_IMAGE"
printf 'no\n' | avdmanager create avd --force -n "$AVD" -k "$API_IMAGE" --device pixel_6 -p "$ANDROID_AVD_HOME/$AVD.avd"
if [[ ! -f "$ANDROID_AVD_HOME/$AVD.ini" && -f "$ANDROID_AVD_HOME/$AVD.avd/config.ini" ]]; then
  printf 'avd.ini.encoding=UTF-8\npath=%s\ntarget=android-36\n' "$ANDROID_AVD_HOME/$AVD.avd" > "$ANDROID_AVD_HOME/$AVD.ini"
fi
ls -la "$ANDROID_AVD_HOME"
test -f "$ANDROID_AVD_HOME/$AVD.avd/config.ini"
test -f "$ANDROID_AVD_HOME/$AVD.ini"
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

# UI interaction uses the real signed APK, not a mock or debug build.
ui_find() {
  local field="$1" target="$2" action="$3"
  for attempt in $(seq 1 5); do
    if adb shell uiautomator dump /sdcard/my-earth-smoke.xml >/dev/null 2>&1 && adb pull /sdcard/my-earth-smoke.xml /tmp/my-earth-smoke.xml >/dev/null 2>&1; then
      local coords
      if coords=$(python3 - "$field" "$target" <<'XMLPY'
import sys,re,xml.etree.ElementTree as ET
field,target=sys.argv[1:]
for node in ET.parse('/tmp/my-earth-smoke.xml').iter('node'):
    if target.casefold() in node.attrib.get(field,'').casefold():
        nums=list(map(int,re.findall(r'\d+',node.attrib.get('bounds',''))))
        if len(nums)==4:
            print((nums[0]+nums[2])//2,(nums[1]+nums[3])//2)
            sys.exit(0)
sys.exit(1)
XMLPY
      ); then
        if [[ "$action" == tap ]]; then adb shell input tap $coords; fi
        echo "PASS: UI $action found $target"
        return 0
      fi
    fi
    sleep 2
  done
  echo "FAILED: UI $target not found"
  cat /tmp/my-earth-smoke.xml || true
  return 1
}
check_running() {
  local label="$1"
  adb logcat -b crash -d > "/tmp/my-earth-$label-crash.txt"
  if grep -F "Process: $PKG" "/tmp/my-earth-$label-crash.txt"; then
    cat "/tmp/my-earth-$label-crash.txt"
    return 1
  fi
  adb shell pidof "$PKG"
  echo "PASS: $label remains running"
}

test -s previous-1047/app-release.apk
adb install previous-1047/app-release.apk
launch_check old-1047
ui_find text English tap
sleep 3
ui_find class android.widget.EditText tap
adb shell input text SmokeTest
ui_find text Save tap
sleep 3
ui_find text SmokeTest check
adb install -r source/app/build/outputs/apk/release/app-release.apk
launch_check upgrade-1048
ui_find text SmokeTest check
# Newly async badge loading must still display the collection.
ui_find content-desc "나의 배지 컬렉션" tap
ui_find text "나의 배지 컬렉션" check
adb shell input keyevent 4
sleep 2
# Pan repeatedly inside the map (relative to actual emulator screen).
read -r width height < <(adb shell wm size | tail -1 | sed -E 's/.* ([0-9]+)x([0-9]+).*/\1 \2/' | tr -d '\r')
for n in $(seq 1 6); do
  adb shell input swipe "$((width/4))" "$((height/3))" "$((width*3/4))" "$((height/3))" 120
  adb shell input swipe "$((width*3/4))" "$((height/3))" "$((width/4))" "$((height*2/5))" 120
done
sleep 4
check_running map-and-badges-1048
# Exercise background/resume without force stop, then a separate relaunch.
adb shell input keyevent 3
sleep 2
adb shell am start -W -n "$ACT"
sleep 4
ui_find text SmokeTest check
check_running resume-1048
launch_check relaunch-1048
ui_find text SmokeTest check
adb uninstall "$PKG"
adb install source/app/build/outputs/apk/release/app-release.apk
launch_check fresh-1048
echo "All 0.10.48 startup, upgrade, badge, map gesture, and resume checks passed."
