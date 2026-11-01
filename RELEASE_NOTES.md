# Nahata AI website + Android companion update

## Website
- Added a persistent `INSTALL APP` header button. It uses the browser install prompt when available and shows platform-specific manual install instructions otherwise.
- Added a website floating N button that opens the mini assistant while the website is open.
- Rebuilt the mini assistant composer in a compact Gemini-inspired layout with plus/file attachment, text input, microphone and send controls.
- Added JARVIS/ULTRON mode switching and mini transcript mirroring.
- Added `ANDROID COMPANION` download CTA. It redirects to `NAHATA_ANDROID_APK_URL` when configured and otherwise explains the publishing setup.
- Updated the offline shell cache version.

## Android companion
- Native floating N bubble: tap opens the website; long-press opens the panel.
- Dynamically discovers apps exposing a normal launcher activity, with search and app launch.
- Adds a user-invoked speech command to find and open a launchable app by spoken name.
- Adds the correct launcher-intent `<queries>` declaration instead of a hard-coded list of four apps.

## Not claimed
- No always-on wake word, locked-screen hotword, universal app access, silent calls, notification access, or arbitrary system control.
- Apps without a public launcher activity and Android-protected packages are not launchable through this companion.
- Android APK compilation/physical-device testing must be completed by GitHub Actions and the user device; no Android SDK is installed in this build environment.
