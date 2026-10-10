from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
import os, uuid, textwrap, zipfile, io, re

app = Flask(__name__)
CORS(app)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
os.makedirs("tmp", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("generated", exist_ok=True)

def create_pdf(text, filepath):
    text = text.replace("**","").replace("##","")
    wrapped=[]
    for para in text.split("\n"):
        wrapped.extend(textwrap.wrap(para, width=85) or [""])
    pages=[wrapped[i:i+55] for i in range(0,len(wrapped),55)] or [["No content"]]
    streams=[]
    for pg in pages:
        s="BT\n/F1 12 Tf\n50 750 Td\n"
        for ln in pg:
            safe=ln.replace("\\","\\\\").replace("(","\\(").replace(")", "\\)")[:90]
            s+=f"({safe}) Tj\n0 -18 Td\n"
        s+="ET"; streams.append(s)
    parts=["%PDF-1.4\n"]; offsets=[0]
    offsets.append(len("".join(parts))); parts.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    kids=" ".join([f"{4+i} 0 R" for i in range(len(pages))])
    offsets.append(len("".join(parts))); parts.append(f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {len(pages)} >> endobj\n")
    offsets.append(len("".join(parts))); parts.append("3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    cstart=4+len(pages)
    for i in range(len(pages)):
        offsets.append(len("".join(parts))); parts.append(f"{4+i} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {cstart+i} 0 R >> endobj\n")
    for i,s in enumerate(streams):
        offsets.append(len("".join(parts))); parts.append(f"{cstart+i} 0 obj << /Length {len(s)} >> stream\n{s}\nendstream endobj\n")
    xref=len("".join(parts)); parts.append(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n")
    for off in offsets[1:]: parts.append(f"{off:010d} 00000 n \n")
    parts.append(f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF")
    open(filepath,"w",encoding="latin-1",errors="ignore").write("".join(parts))

@app.route("/")
def home(): return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg=""
        if 'multipart' in (request.content_type or ""):
            msg=request.form.get("message","")
        else:
            j=request.get_json(silent=True); msg=j.get("message","") if j else ""
        if not msg: msg="Hello"

        # File upload
        if 'file' in request.files:
            f=request.files['file']
            if f.filename:
                name=f"{uuid.uuid4().hex[:6]}_{f.filename}"
                f.save(f"uploads/{name}")
                return jsonify({"reply":f"Got file {f.filename}. Tell me to convert to PDF, ZIP, or edit.","file":f"/view-file/{name}"})

        # Image gen
        if any(k in msg.lower() for k in ["logo","image","photo","thumbnail","poster"]):
            url=f"https://image.pollinations.ai/prompt/{msg}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}"
            return jsonify({"reply":f"Image generated for: {msg}","image":url})

        # Code generation prompt - force file creation
        system = """You are Nahata.AI - full developer.
        If user asks for ID card, website, Raspberry Pi, Arduino, Python app - ALWAYS give full code with filename.
        Format:
        FILENAME: index.html
        ```html
        code here
