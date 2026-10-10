from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
import os, uuid, textwrap, zipfile, re

app = Flask(__name__)
CORS(app)
client = Groq(api_key=os.environ.get("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"))
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
        if 'file' in request.files:
            f=request.files['file']
            if f.filename:
                name=f"{uuid.uuid4().hex[:6]}_{f.filename}"
                f.save(f"uploads/{name}")
                return jsonify({"reply":f"Got file {f.filename}. I can convert to PDF, ZIP, or edit it.","file":f"/view-file/{name}"})
        if any(k in msg.lower() for k in ["logo","image","photo","poster","thumbnail"]):
            url=f"https://image.pollinations.ai/prompt/{msg}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}"
            return jsonify({"reply":f"Image generated for: {msg}","image":url})

        system_prompt = "You are Nahata.AI - full developer. If user asks ID card, website, Raspberry Pi, Arduino, Python app - give full code with FILENAME: filename and code block. For multiple files give multiple. At end say ZIP ready."

        r=client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":system_prompt},{"role":"user","content":msg}])
        reply=r.choices[0].message.content

        files=[]
        pattern = r"FILENAME:\s*([^\n]+)\n```[\w]*\n(.*?)```"
        matches = re.findall(pattern, reply, re.DOTALL)
        if not matches:
            blocks = re.findall(r"```(\w+)?\n(.*?)```", reply, re.DOTALL)
            for i,(lang,code) in enumerate(blocks):
                ext = lang if lang else "txt"
                if ext=="html": fname=f"index_{i}.html"
                elif ext in ["py","python"]: fname=f"main_{i}.py"
                elif ext in ["ino","cpp"]: fname=f"sketch_{i}.ino"
                elif ext in ["js","javascript"]: fname=f"script_{i}.js"
                elif ext=="css": fname=f"style_{i}.css"
                else: fname=f"file_{i}.{ext}"
                files.append((fname,code))
        else:
            for fname,code in matches:
                files.append((fname.strip(),code))
        return jsonify({"reply":reply,"files":files})
    except Exception as e:
        print(e)
        return jsonify({"reply":f"Error: {e}"}),500

@app.route("/make-file", methods=["POST"])
def make_file():
    data=request.get_json()
    fname=data.get("filename","file.txt")
    content=data.get("content","")
    safe_name=f"{uuid.uuid4().hex[:6]}_{fname}"
    path=f"generated/{safe_name}"
    open(path,"w",encoding="utf-8",errors="ignore").write(content)
    return jsonify({"url":f"/download-file/{safe_name}"})

@app.route("/make-zip", methods=["POST"])
def make_zip():
    data=request.get_json()
    files=data.get("files",[])
    fid=uuid.uuid4().hex
    zip_path=f"tmp/{fid}.zip"
    with zipfile.ZipFile(zip_path,'w') as z:
        for item in files:
            z.writestr(item['filename'], item['content'])
    return jsonify({"zip_url":f"/download-zip/{fid}"})

@app.route("/view-file/<name>")
def view_file(name): return send_file(f"uploads/{name}")

@app.route("/download-file/<name>")
def download_file(name): return send_file(f"generated/{name}",as_attachment=True)

@app.route("/download-zip/<fid>")
def download_zip(fid): return send_file(f"tmp/{fid}.zip",as_attachment=True,download_name="NahataAI_Project.zip")

@app.route("/make-pdf", methods=["POST"])
def make_pdf():
    t=request.get_json().get("text",""); fid=uuid.uuid4().hex; p=f"tmp/{fid}.pdf"; create_pdf(t,p); return jsonify({"pdf_url":f"/download-pdf/{fid}"})

@app.route("/download-pdf/<fid>")
def download_pdf(fid): return send_file(f"tmp/{fid}.pdf",as_attachment=True,download_name="NahataAI.pdf")

if __name__ == "__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
