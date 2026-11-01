NAHATA AI — WEBSITE + ANDROID COMPANION UPDATE

WHAT IS INCLUDED
1) website/ — Flask website with the existing AI backend, visible INSTALL APP button, PWA install prompt/fallback, a floating N mini button, Gemini-style mini chat composer, + file attachment button, microphone input, JARVIS/ULTRON switch, and chat responses mirrored in the mini panel.
2) android-companion/ — Android source project. It provides a user-started floating N bubble over other apps. Tap the bubble to open Nahata AI; long-press it to open the native mini panel. The panel discovers launcher-visible apps, lets the user search and open them, and includes a voice app-name command.
3) .github/workflows/build-apk.yml — GitHub Actions build. A manual run builds the companion APK, saves it as a workflow artifact, and publishes a GitHub Release asset named NahataAI-Companion.apk.

WEBSITE DEPLOYMENT
- Copy the CONTENTS of website/ into the root of your existing website repository (server.py, templates/, static/).
- Replace BOTH server.py and templates/index.html with the supplied versions. server.py includes the PWA service-worker cache update and /download/android route.
- Keep your existing requirements.txt, Render start command, and all Render environment variables/API keys. Do not paste API keys into HTML or GitHub.
- Commit and push. Wait for Render to finish deploying.
- The website header has INSTALL APP (PWA) and ANDROID COMPANION buttons.

ANDROID APK BUILD + WEBSITE DOWNLOAD BUTTON
- Upload the android-companion/ folder and the root .github/ folder into the SAME GitHub repository (do not nest .github inside android-companion).
- Open GitHub Actions -> Build Nahata AI Companion APK -> Run workflow.
- The workflow publishes a release asset. Its download address will look like:
  https://github.com/OWNER/REPOSITORY/releases/download/nahata-companion-latest/NahataAI-Companion.apk
- In Render -> Environment, set NAHATA_ANDROID_APK_URL to that exact HTTPS asset URL, then redeploy. The website's ANDROID COMPANION button will then redirect to the APK.
- Until that URL is configured, the website button shows an explanation instead of pretending an APK is available.

ANDROID SETUP
- Install the APK, open Nahata AI Companion, allow Display over other apps, then tap Start floating assistant.
- Tap the floating N bubble to open the website; long-press it to open the native mini panel.
- Use Search an installed app to browse/search apps with a normal Android launcher activity. Tap an app to launch it.
- Tap SAY AN APP NAME and say e.g. “open YouTube”. Android speech recognition availability and microphone permission are required.

IMPORTANT PLATFORM LIMITS
- The website PWA can install and can cache its app shell, but it cannot draw over other apps, intercept an invisible screen-corner gesture, continuously listen while closed/locked, or open every Android package.
- The Android companion supplies the floating overlay and launcher-app discovery. Android intentionally hides protected apps and apps without a launch activity; those cannot be opened by this app. Some manufacturer battery settings may stop the floating service.
- Online Nahata AI chat, file analysis, and web research need internet. The native floating panel and app launcher work offline.
- The companion is user-started and shows a persistent Android notification. It does not silently place calls, read notifications, send messages, or change protected phone settings.
- Voice app recognition uses Android's speech-recognition service; it is not an always-on “Hey Nahata AI” hotword. Screen-off wake-word support is not included.

VALIDATION
Website Python syntax, inline JavaScript syntax, Android manifest XML, and ZIP integrity are checked. This environment does not contain the Android SDK, so an APK has not been compiled here. GitHub Actions performs the Android build; test the resulting APK on your phone before distributing it.
