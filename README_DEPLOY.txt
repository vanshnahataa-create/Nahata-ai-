NAHATA-AI FLUX.2 RENDER PACKAGE

Render Build Command: pip install -r requirements.txt
Render Start Command: gunicorn server:app --timeout 180

Environment variables (Render > service > Environment):
- GROQ_API_KEY = your private Groq API key
- BFL_API_KEY = your private Black Forest Labs API key
- BFL_IMAGE_MODEL = flux-2-pro (server default)
- BFL_API_URL = https://api.bfl.ai/v1 (server default)

Keep API keys secret; never put them in HTML or public GitHub. FLUX.2 API use may cost money and requires valid account access/credits.

The Python server passed a syntax check, but this package has not been tested with your live API keys or deployed on your Render account. After deployment, test chat, image generation, image editing, and Android installation.
