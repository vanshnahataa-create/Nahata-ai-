# Nahata AI Android Companion

This Android companion adds a user-started floating **N** bubble over other apps.

## What it currently does
- Shows a floating N bubble after the user grants Android's Display over other apps permission and starts the service.
- Tap the bubble to open the Nahata AI website.
- Long-press the bubble to open a compact native panel.
- Search and launch apps that Android exposes through a normal `MAIN` + `LAUNCHER` activity.
- Use **SAY AN APP NAME** to invoke Android speech recognition and launch a matching app, for example “open YouTube”.
- The floating panel and app launcher work without mobile data. Online Nahata AI conversations require internet.

## Build the APK (phone-friendly)
1. Upload this `android-companion/` folder to the root of your GitHub repository. Also upload the sibling root `.github/workflows/build-apk.yml` folder from this package.
2. Open GitHub → Actions → **Build Nahata AI Companion APK** → **Run workflow**.
3. The workflow creates a `NahataAI-Companion.apk` artifact and publishes a GitHub Release asset on manual runs.
4. Download the APK from the workflow artifact or release, install it, and open Nahata AI Companion.
5. Allow **Display over other apps**, then tap **Start floating assistant**.
6. Long-press the N bubble to open the native panel. Search apps or tap **SAY AN APP NAME**.

## Publish the APK download button on the website
After the GitHub Actions manual workflow has published a release, copy the release asset's HTTPS URL. In Render → Environment, set:

`NAHATA_ANDROID_APK_URL=https://github.com/OWNER/REPOSITORY/releases/download/nahata-companion-latest/NahataAI-Companion.apk`

Redeploy the website. The website's **DOWNLOAD APK** button will then redirect to the published APK. Until the variable is configured, it displays setup instructions instead of a broken download.

## Important Android limits
- Only apps with a discoverable launcher activity can be listed/launched. Android intentionally hides protected or non-launchable packages; this app cannot open every package regardless of Android policy.
- The voice app-name action uses Android's speech-recognition service and requires microphone permission. It is not an always-on wake phrase.
- The floating service is user-started and displays a persistent notification. Some Android manufacturers may stop it under battery restrictions.
- This companion does not silently place calls, read notifications, send messages, or modify protected settings.
- The native panel currently provides the app launcher and a shortcut to the website chat. The Gemini-style text/file/microphone mini composer is in the website itself; it is not yet embedded inside the native overlay panel.

The project targets Android API 35 and requires Android 8.0 (API 26) or later. Build and test the APK on a physical device before distributing it.
