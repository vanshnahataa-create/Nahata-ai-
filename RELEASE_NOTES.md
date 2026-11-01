# Nahata.AI — validated website package

## What this package contains
- Existing Flask backend: `deploy-package/server.py` (left unchanged)
- Existing website: `deploy-package/templates/index.html`
- Existing PWA icons and social preview assets: `deploy-package/static/`
- Existing mini assistant, voice-command guide, browser wake phrase (while page is visible), and dialer hand-off for a number (user must confirm the call).

## Validation performed
- Python syntax compilation: `python -m py_compile deploy-package/server.py` — PASS.
- Inline JavaScript syntax check with Node.js `node --check` — PASS.
- Archive integrity: package extracted successfully — PASS.

These are syntax/package checks only. They do not prove that external AI providers, API keys, microphone permissions, Android intents, Render deployment, or every device/browser combination work. Those require live integration tests with the deployment's environment variables and a real Android device.

## Website-only limitations (do not present these as implemented)
A website/PWA cannot become Android's system assistant or keep a custom hotword microphone active after the page is closed, the browser is backgrounded, or the phone is locked. Browser wake-word listening in this project is available only while the page is visible and the browser supports SpeechRecognition.

A website can hand a phone number to the dialer using a `tel:` link, but the user must review and confirm the call. It cannot silently call a contact, read the contact book, inspect notifications, freely control system settings, or launch arbitrary installed apps with guaranteed behavior.

For system-level assistant behavior, a separate native Android companion is required. Android's `VoiceInteractionService` is the platform integration point; microphone/background-service access is subject to Android version, assistant selection, permissions, and foreground-service restrictions.

## Deploy
Keep the existing Render service configuration and environment variables. Deploy the contents of `deploy-package/` using the same project layout as the current deployment. Do not replace `server.py` for this website-only validation release.

## No zero-bug guarantee
No software release can honestly be guaranteed to have zero bugs. This package passed the static checks listed above; complete verification still requires staging deployment and device-level tests.

## JARVIS + ULTRON parity update
- Both personalities use the same website-supported voice-command and mini-assistant functions.
- Wake phrase recognises “Hey Nahata AI”, “Hey Jarvis”, and “Hey Ultron” while the page is open, visible, and browser speech recognition is active.
- JARVIS keeps the blue/cyan visual theme and its selected device voice; ULTRON keeps the red visual theme and its independently selected device voice.
- ULTRON is a dramatic fictional persona only; phone actions remain permission-gated and calls require user confirmation.
