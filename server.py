from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os, uuid, textwrap, zipfile, re

app = Flask(__name__)
CORS(app)

print("=== Nahata.AI Starting ===")

# SAFE GROQ - No crash if key missing
client = None
try:
    from groq import Groq
    key = os.environ.get("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")
    if key:
        client = Groq(api_key=key)
        print("Groq OK:", key[:8]+"...")
    else:
        print("WARNING: GROQ_API_KEY not set - dummy mode")
except Exception as e:
    print(f"Groq fail {e} - dummy mode")

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
NAHATA PUBLIC SCHOOL
Annual Examination 2025-26
Subject: {topic.upper()}
Class: 10 | Time: 3 Hours | Max Marks: 80
Made by Vansh Rajesh Nahata - Nahata.AI World Best AI

SECTION A - Objective (10 Marks)
Q1. MCQ (5x1=5)
 a) pi=? (i)3.14 (ii)2.14 (iii)3.0 (iv)4.14
 b) 2x+3=7 x=? (i)1 (ii)2 (iii)3 (iv)4
 c) Area circle? (i)pi*r2 (ii)2*pi*r (iii)l*b (iv)none
 d) 10% of 200? (i)10 (ii)20 (iii)30 (iv)40
 e) Prime 1-10? (i)4 (ii)6 (iii)7 (iv)9
Q2. Fill blanks (5x1=5)
 a) sqrt64=__ b) (a+b)2=__ c) sin90=__ d) HCF12,18=__ e) Probability __ to __

SECTION B - Short Answer (20 Marks)
Q3. Solve 3x+5=20 (2)
Q4. Area triangle base10 height8 (2)
Q5. Factorize x2-9 (2)
Q6. Cost 5 pens Rs100 cost 1? (2)
Q7. Define rational number (2)
Q8. Mean 5,10,15,20,25 (2)
Q9. Prove Pythagoras theorem (4)
Q10. Solve x2-5x+6=0 (4)

SECTION C - Long Answer (30 Marks)
Q11. Train 360km speed+5 time-1hr Find speed (6)
Q12. Construct triangle sides 5,6,7cm (6)
Q13. Shopkeeper marked 20% above gives 10% discount profit%? (6)
Q14. Marks bar graph median calculation (6)
Q15. Sum angles triangle 180 proof (6)

SECTION D - Case Study (20 Marks)
Q16. Garden 20m x15m (10)
 a) Perimeter (2) b) Area (2) c) Fencing Rs10/m cost? (3) d) Path 1m inside area? (3)
Q17. Invest 20000 A 10% interest B profit share (10)
 a) SI A 2yrs (3) b) Profit 5000 ratio2:3 share? (3) c) CI formula explain (4)

--- BEST OF LUCK --- Prepared by Nahata.AI - Vansh Rajesh Nahata
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/car-game")
def car_game():
    return render_template("car-game.html")

@app.route("/game")
def game_redirect():
    return render_template("car-game.html")

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

        # File Upload - VIDEO + PHOTO + ANY FILE - PERFECT NAME
        if "file" in request.files:
            f=request.files["file"]
            if f.filename:
                safe=f"{uuid.uuid4().hex[:6]}_{f.filename}"
                f.save(f"uploads/{safe}")
                ext=f.filename.lower().split(".")[-1]
                if ext in ["mp4","mov","avi","mkv","webm","mp3","wav"]:
                    return jsonify({"reply":f"Video/Audio {f.filename} uploaded! Preview and download keeps real name {f.filename}. Command: {msg}","file":f"/view-file/{safe}","video":f"/view-file/{safe}"})
                return jsonify({"reply":f"File {f.filename} received. Your command: {msg}. Download keeps real name.","file":f"/view-file/{safe}"})

        # IMAGE GENERATION
        if any(k in lower for k in ["logo","image","photo","poster","thumbnail","banner"]) and "question paper" not in lower:
            url=f"https://image.pollinations.ai/prompt/{msg}?width=1024&height=1024&seed={uuid.uuid4().hex[:4]}"
            return jsonify({"reply":f"Image generated for: {msg} - Vansh Rajesh Nahata's Nahata.AI","image":url})

        # QUESTION PAPER - REAL USABLE
        if "question paper" in lower:
            paper=real_question_paper(msg)
            files=[("Question_Paper.txt", paper)]
            return jsonify({"reply":paper,"files":files})

        # If no GROQ key - still work
        if client is None:
            paper=real_question_paper(msg)
            return jsonify({"reply":f"Hello! I am Nahata.AI by Vansh Rajesh Nahata (Add GROQ_API_KEY in Render for full AI). Here is sample for '{msg}':\n\n{paper}","files":[("Question_Paper.txt", paper)]})

        # Full AI
        system_prompt="You are Nahata.AI made by Vansh Rajesh Nahata - World best AI search engine. You make photos, files, pdf, code, videos, 3D games, question papers. For code always give FILENAME: filename and code block. White background black text UI."
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
                elif ext=="ino": fname=f"sketch_{i}.ino"
                files.append((fname,code))
        else:
            for fname,code in matches:
                files.append((fname.strip(),code))
        return jsonify({"reply":reply,"files":files})
    except Exception as e:
        print(f"CHAT ERROR: {e}")
        return jsonify({"reply":f"Server running but error: {e}. Paper still available: {real_question_paper(msg)}","files":[("Question_Paper.txt", real_question_paper(msg))]})

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

# PERFECT DOWNLOAD NAMES - VIDEO WILL BE VIDEO.MP4 NOT PDF
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
    print(f"=== Nahata.AI Running on {port} ===")
    app.run(host="0.0.0.0", port=port)
