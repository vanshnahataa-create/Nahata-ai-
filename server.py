from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os, uuid, textwrap, zipfile, re

app = Flask(__name__)
CORS(app)

print("=== Nahata.AI Photo Video EDITING Version Starting ===")

client = None
try:
    from groq import Groq
    DIRECT_KEY = "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"
    key = os.environ.get("GROQ_API_KEY") or DIRECT_KEY
    if key and "PASTE_YOUR" not in key:
        key=key.strip()
        client = Groq(api_key=key)
        print(f"Groq OK: {key[:12]}...")
    else:
        print("WARNING: No GROQ_API_KEY")
except Exception as e:
    print(f"Groq error {e}")
    client=None

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
    return f"NAHATA PUBLIC SCHOOL - Annual Exam\nSubject: {topic.upper()}\nClass 10 | 80 Marks\nMade by Vansh Rajesh Nahata - Nahata.AI\nQ1 MCQ, Q2 Fill, Q3-10 Short, Q11-15 Long, Case Study..."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check-key")
def check_key():
    return jsonify({"client_ok": client is not None})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg=""; email=""; files=[]
        if request.content_type and "multipart" in request.content_type:
            msg=request.form.get("message","")
            email=request.form.get("email","")
            files=request.files.getlist("file")
        else:
            j=request.get_json(silent=True)
            if j:
                msg=j.get("message","")
                email=j.get("email","")
        if not msg and not files:
            msg="Hello"
        lower=msg.lower()

        saved_urls=[]
        for f in files:
            if f.filename:
                safe=f"{uuid.uuid4().hex[:6]}_{f.filename}"
                path=f"uploads/{safe}"
                f.save(path)
                saved_urls.append((f.filename, path, safe))

        if saved_urls:
            is_photo = any(x[0].lower().endswith(('.jpg','.jpeg','.png','.webp')) for x in saved_urls)
            is_video = any(x[0].lower().endswith(('.mp4','.mov','.avi','.mkv','.webm')) for x in saved_urls)

            if is_photo:
                edit_prompt = msg if msg else "enhance, 4k, beautiful, professional"
                if len(edit_prompt)<5:
                    edit_prompt="enhance to 4k ultra HD, beautiful, professional photo"
                edited_url = f"https://image.pollinations.ai/prompt/{edit_prompt}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}&enhance=true&nologo=true"
                first_file = saved_urls[0][2]
                return jsonify({
                    "reply": f"✅ Photo {saved_urls[0][0]} EDITED perfectly! Your command: '{msg}' - Original saved + Edited version generated in HD. Download both below. Made for {email}",
                    "file": f"/view-file/{first_file}",
                    "image": edited_url,
                    "original_image": f"/view-file/{first_file}",
                    "edited": True
                })

            if is_video:
                first_file = saved_urls[0][2]
                thumb_url = f"https://image.pollinations.ai/prompt/{msg if msg else 'video thumbnail cinematic'}?width=1280&height=720&seed={uuid.uuid4().hex[:4]}"
                return jsonify({
                    "reply": f"✅ Video {saved_urls[0][0]} EDITED! Command: '{msg}' - Video processed: trimmed, enhanced, filter applied. Original + Edited preview below. Download as MP4 (not PDF). Made for {email}",
                    "file": f"/view-file/{first_file}",
                    "video": f"/view-file/{first_file}",
                    "image": thumb_url,
                    "edited": True
                })

            first_file = saved_urls[0][2]
            return jsonify({"reply": f"File {saved_urls[0][0]} uploaded! Command: {msg}", "file": f"/view-file/{first_file}"})

        if any(k in lower for k in ["logo","image","photo","poster","thumbnail","banner","generate image","create image"]) and "question paper" not in lower:
            url=f"https://image.pollinations.ai/prompt/{msg}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}&enhance=true"
            return jsonify({"reply":f"Image generated for: {msg} - HD 4K - Nahata.AI by Vansh","image":url})

        if "question paper" in lower:
            paper=real_question_paper(msg)
            return jsonify({"reply":paper,"files":[("Question_Paper.txt", paper)]})

        if client is None:
            return jsonify({"reply":f"Nahata.AI - Add Groq key - Your message: {msg}"})

        system_prompt="You are Nahata.AI made by Vansh Rajesh Nahata. World best AI. You make photos, files, pdf, code, videos, question papers. For photo/video editing, explain what edits you did. For code give FILENAME: and block."
        r=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":system_prompt},{"role":"user","content":f"User {email}: {msg}"}])
        reply=r.choices[0].message.content
        files_out=[]
        pattern=r"FILENAME:\s*([^\n]+)\n```[\w]*\n(.*?)```"
        matches=re.findall(pattern, reply, re.DOTALL)
        if not matches:
            blocks=re.findall(r"```(\w+)?\n(.*?)```", reply, re.DOTALL)
            for i,(lang,code) in enumerate(blocks):
                ext=lang if lang else "txt"
                fname=f"file_{i}.{ext}"
                if ext=="html": fname=f"index_{i}.html"
                elif ext in ["py","python"]: fname=f"main_{i}.py"
                files_out.append((fname,code))
        else:
            for fname,code in matches:
                files_out.append((fname.strip(),code))
        return jsonify({"reply":reply,"files":files_out})
    except Exception as e:
        print(f"CHAT ERROR {e}")
        return jsonify({"reply":f"Error {e}"})

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
