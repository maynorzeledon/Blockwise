#!/usr/bin/env bash
set -euo pipefail
mkdir -p android-test-results
adb install -r "$(find apk -name app-debug.apk -print -quit)"
adb install -r "$(find apk -name app-debug-androidTest.apk -print -quit)"
trap 'adb pull /sdcard/Android/data/com.mayprep.blockwise/files android-test-results/screenshots || true' EXIT
adb shell settings put secure show_ime_with_hard_keyboard 1
for mode in threebutton gestural; do
  adb shell cmd overlay enable-exclusive --category "com.android.internal.systemui.navbar.$mode"
  adb shell am instrument -w -r -e navMode "$mode" com.mayprep.blockwise.test/androidx.test.runner.AndroidJUnitRunner | tee "android-test-results/$mode.txt"
  grep -E 'OK \([0-9]+ tests?\)' "android-test-results/$mode.txt"
done
