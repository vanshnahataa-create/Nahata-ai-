NAHATA.AI — Render PWA package (FLUX.2 configuration)

Files:
- server.py: Flask backend
- templates/index.html: website UI and install prompt
- static/: app icons
- requirements.txt: Python dependencies

RENDER
Build command: pip install -r requirements.txt
Start command: gunicorn server:app --timeout 180

Environment variables (add only keys you own):
GROQ_API_KEY = your Groq key
BFL_API_KEY = your Black Forest Labs key
BFL_IMAGE_MODEL = flux-2-pro

Important:
- The site must be served over HTTPS for PWA installation.
- On Android, use updated Chrome. The website's Install button calls the browser's native install prompt when Chrome provides it. Android/Chrome still controls final confirmation; a website cannot silently install an app without user approval.
- If native install prompt is unavailable, the button explains the Chrome menu fallback.
- After deployment, reload the site. If an older installed shortcut has the old icon, remove that shortcut and install again. Browser caches may delay icon updates.
- FLUX.2 endpoint/model configuration is set in the server, but API calls and account credits must be tested with your own key. This package has not been deployed to your Render account.
