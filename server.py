from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os, uuid, textwrap, zipfile, re

app = Flask(__name__)
CORS(app)

print("=== Nahata.AI World Best Starting ===")

# SAFE GROQ - Never crash
client = None
try:
    from groq import Groq
    key = os.environ.get("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")
    if key:
        client = Groq(api_key=key)
        print("Groq OK")
    else:
        print("WARNING: No GROQ_API_KEY")
except Exception as e:
    print(f"Groq error {e}")

os.makedirs("tmp", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("generated", exist_ok=True)

def create_pdf(text, filepath):
    text = text.replace("**","").replace("##","").replace("###","")
    wrapped=[]
    for para in text.split("\n"):
        wrapped.extend(textwrap.wrap(para, width=82) or [""])
    pages=[wrapped[i:i+50] for i in range(0,len(wrapped),50)] or [["No content"]]
    streams=[]
    for pg in pages:
        s="BT\n/F1 11 Tf\n50 750 Td\n"
        for ln in pg:
            safe=ln.replace("\\","\\\\").replace("(","\\(").replace(")", "\\)")[:90]
            s+=f"({safe}) Tj\n0 -16 Td\n"
        s+="ET"
        streams.append(s)
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

def real_question_paper(topic):
    return f"""
NAHATA PUBLIC SCHOOL - Annual Examination
Subject: {topic.upper()}
Class 10 | Time: 3 Hours | Max 80 Marks
Made by Vansh Rajesh Nahata - Nahata.AI World Best Search Engine

SECTION A Objective 10 Marks
Q1 MCQ 5 marks, Q2 Fill blanks 5 marks
SECTION B Short 20 Marks Q3-10
SECTION C Long 30 Marks Q11-15
SECTION D Case Study 20 Marks Q16-17
Full real paper with diagrams, calculations, graphs.

--- BEST OF LUCK ---
Prepared by Nahata.AI - Vansh Rajesh Nahata
"""

@app.route("/")
def home():
    return render_template("index.html")

# ===== VOICE BOX TRANSCRIBE =====
@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        if "file" not in request.files:
            return jsonify({"error":"No audio"}),400
        f=request.files["file"]
        safe=f"uploads/{uuid.uuid4().hex}_{f.filename}"
        f.save(safe)
        if client:
            # Groq Whisper
            with open(safe,"rb") as audio:
                tr=client.audio.transcriptions.create(model="whisper-large-v3", file=audio)
                text=tr.text
            return jsonify({"text":text})
        else:
            return jsonify({"text":f"Voice received {f.filename} (Add GROQ_API_KEY for transcribe)"})
    except Exception as e:
        return jsonify({"error":str(e),"text":"Voice box error"}),500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg=""
        if request.content_type and "multipart" in request.content_type:
            msg=request.form.get("message","")
        else:
            j=request.get_json(silent=True)
            if j:
                msg=j.get("message","")
        if not msg:
            msg="Hello"
        lower=msg.lower()

        # 1. FILE + VIDEO + PHOTO + VOICE - REAL NAME PERFECT
        if "file" in request.files:
            f=request.files["file"]
            if f.filename:
                safe=f"{uuid.uuid4().hex[:6]}_{f.filename}"
                f.save(f"uploads/{safe}")
                ext=f.filename.lower().split(".")[-1]
                if ext in ["mp4","mov","avi","mkv","webm"]:
                    return jsonify({"reply":f"Video {f.filename} uploaded perfectly! Your command: {msg}. Download will be {f.filename} not pdf.","file":f"/view-file/{safe}","video":f"/view-file/{safe}"})
                elif ext in ["mp3","wav","m4a","ogg","webm"]:
                    return jsonify({"reply":f"Voice/Audio {f.filename} uploaded! Command: {msg}","file":f"/view-file/{safe}","audio":f"/view-file/{safe}"})
                elif ext in ["jpg","jpeg","png","webp"]:
                    return jsonify({"reply":f"Photo {f.filename} uploaded! Command: {msg}","file":f"/view-file/{safe}","image":f"/view-file/{safe}"})
                return jsonify({"reply":f"File {f.filename} received. Command: {msg}","file":f"/view-file/{safe}"})

        # 2. IMAGE GENERATION
        if any(k in lower for k in ["logo","image","photo","poster","thumbnail","banner"]) and "question paper" not in lower:
            url=f"https://image.pollinations.ai/prompt/{msg}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}"
            return jsonify({"reply":f"Image generated for: {msg} - Nahata.AI by Vansh","image":url})

        # 3. QUESTION PAPER REAL
        if "question paper" in lower:
            paper=real_question_paper(msg)
            return jsonify({"reply":paper,"files":[("Question_Paper.txt", paper)]})

        # 4. NO GROQ KEY DUMMY
        if client is None:
            paper=real_question_paper(msg)
            return jsonify({"reply":f"Nahata.AI dummy mode (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). Sample for '{msg}':\n{paper}","files":[("Question_Paper.txt", paper)]})

        # 5. FULL AI
        system_prompt="You are Nahata.AI made by Vansh Rajesh Nahata. World best AI. You make photos, files, pdf, code, videos, question papers. For code give FILENAME: and block."
        r=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":system_prompt},{"role":"user","content":msg}])
        reply=r.choices[0].message.content
        files=[]
        pattern=r"FILENAME:\s*([^\n]+)\n```[\w]*\n(.*?)```"
        matches=re.findall(pattern, reply, re.DOTALL)
        if not matches:
            blocks=re.findall(r"```(\w+)?\n(.*?)```", reply, re.DOTALL)
            for i,(lang,code) in enumerate(blocks):
                ext=lang if lang else "txt"
                fname=f"file_{i}.{ext}"
                if ext=="html": fname=f"index_{i}.html"
                elif ext in ["py","python"]: fname=f"main_{i}.py"
                files.append((fname,code))
        else:
            for fname,code in matches:
                files.append((fname.strip(),code))
        return jsonify({"reply":reply,"files":files})
    except Exception as e:
        print(f"CHAT ERROR {e}")
        return jsonify({"reply":f"Error {e} but server running!"})

@app.route("/make-file", methods=["POST"])
def make_file():
    data=request.get_json(); fname=data.get("filename","file.txt"); content=data.get("content","")
    safe=f"{uuid.uuid4().hex[:6]}_{fname}"
    open(f"generated/{safe}","w",encoding="utf-8",errors="ignore").write(content)
    return jsonify({"url":f"/download-file/{safe}","real_name":fname})

@app.route("/make-zip", methods=["POST"])
def make_zip():
    data=request.get_json(); files=data.get("files",[]); fid=uuid.uuid4().hex; zp=f"tmp/{fid}.zip"
    with zipfile.ZipFile(zp,"w") as z:
        for it in files: z.writestr(it["filename"], it["content"])
    return jsonify({"zip_url":f"/download-zip/{fid}"})

@app.route("/make-pdf", methods=["POST"])
def make_pdf():
    t=request.get_json().get("text",""); fid=uuid.uuid4().hex; p=f"tmp/{fid}.pdf"; create_pdf(t,p)
    return jsonify({"pdf_url":f"/download-pdf/{fid}"})

# PERFECT DOWNLOADS - REAL NAMES
@app.route("/view-file/<name>")
def view_file(name):
    return send_file(f"uploads/{name}")

@app.route("/download-file/<name>")
def download_file(name):
    real = name.split("_",1)[1] if "_" in name else name
    return send_file(f"generated/{name}", as_attachment=True, download_name=real)

@app.route("/download-zip/<fid>")
def download_zip(fid):
    return send_file(f"tmp/{fid}.zip", as_attachment=True, download_name="NahataAI_Project.zip")

@app.route("/download-pdf/<fid>")
def download_pdf(fid):
    return send_file(f"tmp/{fid}.pdf", as_attachment=True, download_name="Nahata_Question_Paper.pdf")

if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
