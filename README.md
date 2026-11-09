# TGX Studio — Cloud Android Build

This repository uses GitHub Actions so the Android APK can be built from an Android phone without Android Studio or a local SDK.

## Status and safety

- `tgx/cloud-build` is the cloud-build setup branch. A pull request to `main` is needed before these manually triggered workflows appear in the Actions tab: GitHub only accepts `workflow_dispatch` events when the workflow file exists on the default branch. The changes are not merged automatically.
- The original NimarkoGram workflow builds upstream source without applying the TGX branding patch.
- The TGX Studio Phase 1 workflow first builds the original upstream APK as a baseline gate, then applies a small, exact-match branding patch and builds TGX.
- The current Phase 1 patch changes the app label, application ID and launcher icon. The Light/Dark/System selector and a custom splash-screen redesign are **not implemented yet**.
- APKs are not considered available until a workflow run succeeds and the APK artifact appears.
- The standalone build is unsigned by default per NimarkoGram's BUILDING.md. The workflows therefore sign each output with a newly generated, temporary CI-only debug certificate. No release keystore is created, stored, or committed. Because the certificate is ephemeral per workflow run, uninstall a previous TGX test APK before installing a later run; this is not a production release-signing setup.
- Source is fetched from `Ettacent/NimarkoGram` with recursive submodules. The exact upstream commit and submodule SHAs are saved as artifacts.
- NimarkoGram is GPL-2.0. Preserve upstream notices and make corresponding source available when distributing binaries, in accordance with applicable license terms.

## 1. Add Telegram API credentials once

In this repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `TG_API_ID`: your numeric Telegram API ID from [my.telegram.org](https://my.telegram.org)
- `TG_API_HASH`: your 32-character Telegram API hash

These values are used only to generate the runner's temporary `private.properties`. That file is never committed or uploaded as an artifact. Do not paste the values into chat, workflow YAML, or source code.

## 2. Run the original NimarkoGram build

1. Open the [Actions tab](../../actions).
2. Select **NimarkoGram original APK**.
3. Tap **Run workflow**.
4. Leave `upstream_ref` as `main` for the current upstream branch, or enter a known branch, tag or commit SHA.
5. Open the run and wait. Native compilation may take a long time.
6. If successful, download `nimarkogram-original-apk` under **Artifacts**. Also download `nimarkogram-original-build-logs` if you need the build log and submodule report.

## 3. Run TGX Studio Phase 1

1. Open **Actions → TGX Studio Phase 1 APK → Run workflow**.
2. Use the same `upstream_ref` you used for the baseline build if you want the same source revision.
3. The workflow builds the original app first. If that baseline build fails, it stops before applying TGX branding.
4. If both builds succeed, download `tgx-studio-phase1-apk`, `nimarkogram-original-baseline-apk`, and `tgx-phase1-build-logs` from that run. The original APK is copied aside before the branding patch so the two APK artifacts are not accidentally identical.

## 4. Install the APK on Android

1. Download the APK artifact from the workflow run's **Artifacts** section. GitHub downloads artifacts as ZIP files.
2. Open the ZIP in Files/Downloads and extract the `.apk` file.
3. Tap the APK. If Android blocks the installation, open the prompted settings and allow **Install unknown apps** for the browser or file manager you used.
4. Return to the installer and install the app.

The TGX package ID is `app.tgxstudio.messenger`; it is a separate app from NimarkoGram. Each workflow run creates a fresh temporary debug certificate, so uninstall an earlier TGX test APK before installing a later run. These builds are for testing only, not stable release updates.

## 5. If the workflow fails

- Open the failed run and inspect the first red step.
- Download the logs artifact if it was produced; it includes Gradle output, upstream SHA and recursive submodule status.
- If no APK artifact is present, no successful APK was produced. Do not treat a green checkout step as a successful build.
- Do not upload `private.properties`, API hashes, release keystores, or signing passwords to Issues or artifacts.

## Toolchain pinned to NimarkoGram's build guide

- JDK 17
- Android SDK 36
- Android Build Tools 36.0.0
- Android NDK 26.3.11579264
- CMake 3.22.1
- Python 3.11 for Chaquopy
- Repository Gradle Wrapper
- Task: `:TMessagesProj_AppStandalone:assembleAfatStandalone`
