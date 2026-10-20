Nahata.AI deployment package

Folder layout:
- server.py
- requirements.txt
- templates/index.html
- static/icon-192.png
- static/icon-512.png
- static/icon-maskable-512.png
- static/apple-touch-icon.png

Render settings:
Build command: pip install -r requirements.txt
Start command: gunicorn server:app --timeout 150

Free human-sounding voice:
The /tts route uses Edge TTS voices by default (Jarvis: en-GB-RyanNeural; Ultron: en-US-ChristopherNeural), with optional ElevenLabs if configured. Edge TTS is online and depends on a third-party service; it is not guaranteed unlimited or permanently available. No API key is needed for the default voice path, but the host must install requirements.txt and have internet access.

PWA install:
Deploy the whole folder structure. The app must be served over HTTPS (Render does this). On supported Android browsers, use the Install button when the browser offers installation. Otherwise open the browser menu and choose Install app/Add to Home screen. The install banner cannot force Android to install without the user's confirmation.

Keep all existing environment variables for AI/chat/image/video features in Render. Do not replace your existing secrets with the sample values.


If the install icon is missing or install does not work:
1. Make sure these exact files are in your GitHub repository: static/icon-192.png, static/icon-512.png, static/icon-maskable-512.png, and templates/index.html. Keep the rest of your project files too.
2. Deploy the changes to Render and wait until deployment says Live.
3. On Android Chrome, uninstall/remove the old Nahata.AI shortcut first. Open the website in Chrome, tap the three-dot menu > Settings > Site settings > Storage (or delete site data for the site), then reload the website.
4. Open https://your-site/manifest.webmanifest and confirm it returns JSON with the icon paths /static/icon-192.png?v=5 and /static/icon-512.png?v=5. Open https://your-site/static/icon-192.png?v=5 directly; the image should appear, not a 404/error page.
5. In Chrome, tap the three-dot menu > Install app (or Add to Home screen). The custom banner cannot force the browser's install dialog when Chrome has not fired its install event.
6. Use HTTPS and a supported browser. Keep server.py at the repository root and preserve other project files/environment variables.
