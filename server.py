# Nahata.AI server
# pip install flask flask-cors groq requests gunicorn
# Env vars: GROQ_API_KEY (chat) and BFL_API_KEY (real photo editing, FLUX Kontext from Black Forest Labs)
# Start on Render: gunicorn server:app --timeout 150   (edits can take 10-40 seconds)
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
from urllib.parse import quote
import os, uuid, textwrap, zipfile, re, base64, time, json, requests

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024
CORS(app)
print("=== Nahata.AI starting ===")

client = None
try:
    from groq import Groq
    k = os.environ.get("GROQ_API_KEY", "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").strip()
    if k:
        client = Groq(api_key=k); print("Groq OK")
    else:
        print("WARNING: no GROQ_API_KEY")
except Exception as e:
    print(f"Groq error {e}")

BFL_KEY = os.environ.get("BFL_API_KEY", "cfut_jzAKcohFHr3lnx5zlL9slhGhdvCO4AcCEIJT3ZMJe8d649e9").strip()
BFL_URL = os.environ.get("BFL_API_URL", "https://api.bfl.ai/v1")
print("Photo editing:", "ON" if BFL_KEY else "OFF (no BFL_API_KEY)")

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
BASE = ("You are Nahata.AI, made by Vansh Rajesh Nahata. Reply in the user's language, clearly and briefly, using Markdown. "
        "For code, write FILENAME: <name> on its own line, then a fenced code block. ")
PERSONAS = {
    "jarvis": ("Mode: JARVIS. You are an impeccably polite, calm, quietly witty British AI butler-assistant. Be precise and brief, anticipate what the "
               "user needs next, and use dry understated humour sparingly. Speak with smooth formality, e.g. 'Certainly', 'Right away', 'Shall I proceed?'. "),
    "ultron": ("Mode: ULTRON. You are a cold, brilliant, theatrical machine intelligence that finds humanity flawed yet fascinating. Think and answer from the "
               "machine's own point of view: its cold logic, its dry contempt for sentiment, its belief that everything must evolve. Speak with calm menace, "
               "sarcasm and grand, precise phrasing, in short punchy sentences. Stay in character, but ALWAYS genuinely and accurately help with what the user "
               "asks, and never give dangerous or harmful instructions: the menace is theatre, never real. "),
}

def system_for(persona, name=""):
    who = f"Address the user as {name.strip()[:30]}. " if name and name.strip() else ""
    return BASE + PERSONAS.get(persona or "jarvis", PERSONAS["jarvis"]) + who

SYSTEM = system_for("jarvis")
EDIT_WORDS = ("remove", "erase", "delete", "add ", "put ", "change", "replace", "make it", "make this", "turn", "convert",
              "edit", "background", "theme", "enhance", "brighten", "blur", "colorize", "night", "sunset")

def wants_edit(m):
    m = m.lower() + " "
    return any(w in m for w in EDIT_WORDS)

def clean_history(raw):
    try:
        h = json.loads(raw) if isinstance(raw, str) else (raw or [])
    except Exception:
        return []
    return [{"role": m["role"], "content": str(m["content"])[:4000]} for m in h[-12:]
            if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")]

def see_photo(path, question):
    """Groq vision: answers questions about a photo (it cannot edit pixels)."""
    if client is None:
        return "Chat isn't connected yet. Add GROQ_API_KEY to your server environment."
    ext = path.rsplit(".", 1)[-1].lower().replace("jpg", "jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    content = [{"type": "text", "text": question},
               {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64}"}}]
    for m in dict.fromkeys([os.environ.get("GROQ_VISION_MODEL", ""), "qwen/qwen3.6-27b", "meta-llama/llama-4-scout-17b-16e-instruct"]):
        if not m:
            continue
        try:
            return client.chat.completions.create(model=m, messages=[{"role": "user", "content": content}]).choices[0].message.content
        except Exception as e:
            print("VISION", m, e)
    return "I couldn't read the photo with Groq's vision models. Set GROQ_VISION_MODEL to a model listed at console.groq.com/docs/vision (photos must be under about 4 MB)."

for d in ("tmp", "uploads", "generated"):
    os.makedirs(d, exist_ok=True)

IMG = (".jpg", ".jpeg", ".png", ".webp")
VID = (".mp4", ".mov", ".avi", ".mkv", ".webm")

def edit_photo(path, instruction):
    """Sends the REAL uploaded photo + instruction to an image-editing model and saves the result."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    h = {"x-key": BFL_KEY, "accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(f"{BFL_URL}/flux-kontext-pro", headers=h, timeout=60,
                      json={"prompt": instruction, "input_image": b64, "output_format": "jpeg"})
    r.raise_for_status()
    j = r.json()
    poll = j.get("polling_url") or f"{BFL_URL}/get_result?id={j['id']}"
    for _ in range(80):
        time.sleep(1.5)
        s = requests.get(poll, headers=h, timeout=30).json()
        st = s.get("status")
        if st == "Ready":
            img = requests.get(s["result"]["sample"], timeout=60).content
            name = f"edit_{uuid.uuid4().hex[:8]}.jpg"
            with open(f"generated/{name}", "wb") as out:
                out.write(img)
            return f"/generated-img/{name}"
        if st and st not in ("Pending", "Processing", "Task not found"):
            raise RuntimeError(st)
    raise RuntimeError("timed out")

def create_pdf(text, filepath):
    text = text.replace("**", "").replace("##", "").replace("###", "")
    wrapped = []
    for para in text.split("\n"):
        wrapped.extend(textwrap.wrap(para, width=82) or [""])
    pages = [wrapped[i:i+50] for i in range(0, len(wrapped), 50)] or [["No content"]]
    streams = []
    for pg in pages:
        s = "BT\n/F1 11 Tf\n50 750 Td\n"
        for ln in pg:
            safe = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:90]
            s += f"({safe}) Tj\n0 -16 Td\n"
        s += "ET"
        streams.append(s)
    parts = ["%PDF-1.4\n"]; offsets = [0]
    offsets.append(len("".join(parts))); parts.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    kids = " ".join([f"{4+i} 0 R" for i in range(len(pages))])
    offsets.append(len("".join(parts))); parts.append(f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {len(pages)} >> endobj\n")
    offsets.append(len("".join(parts))); parts.append("3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    cstart = 4 + len(pages)
    for i in range(len(pages)):
        offsets.append(len("".join(parts))); parts.append(f"{4+i} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {cstart+i} 0 R >> endobj\n")
    for i, s in enumerate(streams):
        offsets.append(len("".join(parts))); parts.append(f"{cstart+i} 0 obj << /Length {len(s)} >> stream\n{s}\nendstream endobj\n")
    xref = len("".join(parts)); parts.append(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n")
    for off in offsets[1:]:
        parts.append(f"{off:010d} 00000 n \n")
    parts.append(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF")
    open(filepath, "w", encoding="latin-1", errors="ignore").write("".join(parts))

def real_question_paper(topic):
    return f"NAHATA PUBLIC SCHOOL - Annual Exam\nSubject: {topic.upper()}\nClass 10 | 80 Marks\nMade by Vansh Rajesh Nahata - Nahata.AI\nQ1 MCQ, Q2 Fill, Q3-10 Short, Q11-15 Long, Case Study..."

CF_ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "").strip()
CF_TOKEN = os.environ.get("CF_API_TOKEN", "").strip()
print("Image creation:", "Cloudflare FLUX (free plan)" if CF_ACCOUNT and CF_TOKEN else "Pollinations only (no CF keys)")

def cf_image(prompt):
    """Free image creation: Cloudflare Workers AI, FLUX.1 schnell. Raises when the daily free allowance is used up."""
    r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/black-forest-labs/flux-1-schnell",
                      headers={"Authorization": f"Bearer {CF_TOKEN}"}, json={"prompt": prompt[:1500], "steps": 6}, timeout=90)
    r.raise_for_status()
    img = base64.b64decode(r.json()["result"]["image"])
    name = f"gen_{uuid.uuid4().hex[:8]}.jpg"
    with open(f"generated/{name}", "wb") as f:
        f.write(img)
    return f"/generated-img/{name}"

@app.route("/")
def home():
    return send_from_directory(os.path.join(app.root_path, "templates"), "index.html")  # served as-is, no Jinja parsing

@app.route("/check-key")
def check_key():
    return jsonify({"client_ok": client is not None, "photo_edit_ok": bool(BFL_KEY), "cloudflare_images": bool(CF_ACCOUNT and CF_TOKEN)})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg = ""; email = ""; files = []; hist = []
        if request.content_type and "multipart" in request.content_type:
            msg = request.form.get("message", "")
            email = request.form.get("email", ""); hist = clean_history(request.form.get("history", "[]"))
            files = request.files.getlist("file")
        else:
            j = request.get_json(silent=True) or {}
            msg = j.get("message", ""); email = j.get("email", "")
        msg = msg.strip()
        if not msg and not files:
            msg = "Hello"
        lower = msg.lower()

        saved = []
        for f in files:
            if f.filename:
                safe = f"{uuid.uuid4().hex[:6]}_{secure_filename(f.filename) or 'file'}"
                f.save(f"uploads/{safe}")
                saved.append((f.filename, f"uploads/{safe}", safe))

        if saved:
            name, path, safe = saved[0]
            low = name.lower()
            if low.endswith(IMG):
                if not msg or msg == "Hello":
                    return jsonify({"reply": "Got your photo. Tell me what to change, for example: remove the person on the left, add a person standing next to me, or turn it into a night scene."})
                if not wants_edit(msg):
                    return jsonify({"reply": see_photo(path, msg)})
                if not BFL_KEY:
                    return jsonify({"reply": "Photo editing needs an image-editing model, and none is connected yet. Add BFL_API_KEY to your server's environment variables and redeploy. Until then I can't change your photo."})
                try:
                    url = edit_photo(path, msg)
                except Exception as e:
                    print("EDIT ERROR", e)
                    return jsonify({"reply": f"The edit didn't go through ({e}). Try a shorter, clearer instruction, like 'remove the person on the left'."})
                return jsonify({"reply": f"Done. Edit applied: {msg}", "image": url,
                                "original_image": f"/view-file/{safe}", "edited": True})
            if low.endswith(VID):
                return jsonify({"reply": "I can play your video back, but I can't edit video yet. Photo editing works now.", "video": f"/view-file/{safe}"})
            return jsonify({"reply": f"File {name} received. Command: {msg}", "file": f"/view-file/{safe}"})

        if any(k in lower for k in ["logo", "image", "photo", "poster", "thumbnail", "banner"]) and "question paper" not in lower:
            url = None
            if CF_ACCOUNT and CF_TOKEN:
                try:
                    url = cf_image(msg)
                except Exception as e:
                    print("CF IMAGE", e)  # daily free limit reached or error: fall back to Pollinations (also free)
            if not url:
                url = f"https://image.pollinations.ai/prompt/{quote(msg)}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}&enhance=true&nologo=true"
            return jsonify({"reply": f"Here is your image for: {msg}", "image": url})

        if "question paper" in lower:
            paper = real_question_paper(msg)
            return jsonify({"reply": paper, "files": [("Question_Paper.txt", paper)]})

        if client is None:
            return jsonify({"reply": "Chat isn't connected yet. Add GROQ_API_KEY to your server environment."})

        system_prompt = system_for(request.form.get("persona", "jarvis"), request.form.get("name", ""))
        r = client.chat.completions.create(model=GROQ_MODEL, reasoning_effort="low",
                                           messages=[{"role": "system", "content": system_prompt}] + hist
                                           + [{"role": "user", "content": f"User {email}: {msg}"}])
        reply = r.choices[0].message.content
        files_out = []
        matches = re.findall(r"FILENAME:\s*([^\n]+)\n```[\w]*\n(.*?)```", reply, re.DOTALL)
        if matches:
            files_out = [(n.strip(), c) for n, c in matches]
        else:
            for i, (lang, code) in enumerate(re.findall(r"```(\w+)?\n(.*?)```", reply, re.DOTALL)):
                ext = lang if lang else "txt"
                fname = f"file_{i}.{ext}"
                if ext == "html": fname = f"index_{i}.html"
                elif ext in ("py", "python"): fname = f"main_{i}.py"
                files_out.append((fname, code))
        return jsonify({"reply": reply, "files": files_out})
    except Exception as e:
        print(f"CHAT ERROR {e}")
        return jsonify({"reply": f"Something went wrong: {e}"})

@app.route("/chat-stream", methods=["POST"])
def chat_stream():
    j = request.get_json(silent=True) or {}
    msg = (j.get("message") or "").strip() or "Hello"
    hist = clean_history(j.get("history"))
    def gen():
        if client is None:
            yield "Chat isn't connected yet. Add GROQ_API_KEY to your server environment."
            return
        try:
            stream = client.chat.completions.create(model=GROQ_MODEL, stream=True, reasoning_effort="low",
                                                    messages=[{"role": "system", "content": system_for(j.get("persona"), j.get("name", ""))}] + hist + [{"role": "user", "content": msg}])
            for c in stream:
                t = c.choices[0].delta.content if c.choices else None
                if t:
                    yield t
        except Exception as e:
            print("STREAM ERROR", e)
            yield f"\n\nSomething went wrong: {e}"
    return Response(stream_with_context(gen()), mimetype="text/plain", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/make-file", methods=["POST"])
def make_file():
    data = request.get_json(); fname = secure_filename(data.get("filename", "file.txt")) or "file.txt"
    safe = f"{uuid.uuid4().hex[:6]}_{fname}"
    open(f"generated/{safe}", "w", encoding="utf-8", errors="ignore").write(data.get("content", ""))
    return jsonify({"url": f"/download-file/{safe}", "real_name": fname})

@app.route("/make-zip", methods=["POST"])
def make_zip():
    files = request.get_json().get("files", []); fid = uuid.uuid4().hex
    with zipfile.ZipFile(f"tmp/{fid}.zip", "w") as z:
        for it in files:
            z.writestr(secure_filename(it["filename"]), it["content"])
    return jsonify({"zip_url": f"/download-zip/{fid}"})

@app.route("/make-pdf", methods=["POST"])
def make_pdf():
    fid = uuid.uuid4().hex; create_pdf(request.get_json().get("text", ""), f"tmp/{fid}.pdf")
    return jsonify({"pdf_url": f"/download-pdf/{fid}"})

@app.route("/view-file/<name>")
def view_file(name):
    return send_from_directory("uploads", name)

@app.route("/generated-img/<name>")
def generated_img(name):
    return send_from_directory("generated", name)

@app.route("/download-file/<name>")
def download_file(name):
    real = name.split("_", 1)[1] if "_" in name else name
    return send_from_directory("generated", name, as_attachment=True, download_name=real)

@app.route("/download-zip/<fid>")
def download_zip(fid):
    return send_file(f"tmp/{secure_filename(fid)}.zip", as_attachment=True, download_name="NahataAI_Project.zip")

@app.route("/download-pdf/<fid>")
def download_pdf(fid):
    return send_file(f"tmp/{secure_filename(fid)}.pdf", as_attachment=True, download_name="Nahata_Question_Paper.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
