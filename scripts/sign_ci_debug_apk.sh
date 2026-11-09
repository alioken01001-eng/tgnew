#!/usr/bin/env bash
# Sign an unsigned standalone APK with an ephemeral CI-only debug certificate.
# This is not a release key and is never uploaded or committed.
set -euo pipefail

APK_PATH="${1:?Usage: sign_ci_debug_apk.sh path/to/app.apk}"
if [[ ! -f "$APK_PATH" ]]; then
  echo "::error::APK not found: $APK_PATH"
  exit 1
fi

BUILD_TOOLS_VERSION="36.0.0"
APKSIGNER="$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION/apksigner"
if [[ ! -x "$APKSIGNER" ]]; then
  echo "::error::apksigner not found at $APKSIGNER"
  exit 1
fi

KEYSTORE="$RUNNER_TEMP/tgx-ci-debug.keystore"
SIGNED_APK="$RUNNER_TEMP/tgx-ci-signed.apk"
trap 'rm -f "$KEYSTORE" "$SIGNED_APK"' EXIT

keytool -genkeypair -noprompt -v \
  -keystore "$KEYSTORE" -storetype JKS \
  -storepass android -alias androiddebugkey -keypass android \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"

"$APKSIGNER" sign \
  --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android \
  --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true \
  --out "$SIGNED_APK" "$APK_PATH"

"$APKSIGNER" verify --verbose "$SIGNED_APK"
mv "$SIGNED_APK" "$APK_PATH"
echo "APK signed with a temporary CI debug certificate (not a release key)."
