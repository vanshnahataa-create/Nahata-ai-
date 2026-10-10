from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
import os
import uuid

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
os.makedirs("tmp", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# PURE PYTHON PDF - NO LIBRARY
def create_pdf(text, filepath):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = safe.split("\n")
    stream = "BT\n/F1 12 Tf\n50 750 Td\n"
    for line in lines[:60]:
        if not line.strip():
            stream += "0 -18 Td\n"
            continue
        line = line[:90]
        stream += f"({line}) Tj\n0 -18 Td\n"
    stream += "ET"
    pdf_content = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length {len(stream)} >> stream
{stream}
endstream endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000265 00000 n
0000000338 00000 n
trailer << /Size 6 /Root 1 0 R >>
startxref
{338 + len(stream)}
%%EOF"""
    with open(filepath, "w", encoding="latin-1", errors="ignore") as f:
        f.write(pdf_content)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg = request.form.get("message","") if request.form else ""
        if not msg:
            data = request.get_json(silent=True)
            if data:
                msg = data.get("message","")

        # File upload check
        uploaded_info = ""
        if 'file' in request.files:
            file = request.files['file']
            if file.filename!= '':
                fid = uuid.uuid4().hex[:8]
                ext = file.filename.split('.')[-1]
                save_path = f"uploads/{fid}_{file.filename}"
                file.save(save_path)
                uploaded_info = f" [User uploaded file: {file.filename}]"
                # If image
                if ext.lower() in ['jpg','jpeg','png','webp']:
                    return jsonify({
                        "reply": f"Nice! I received your photo: {file.filename}. What you want me to do? Remove background, make logo, convert to PDF?",
                        "image": f"/view-file/{fid}_{file.filename}",
                        "is_upload": True
                    })

        if "logo" in msg.lower() or "image" in msg.lower() or "photo" in msg.lower():
            img_url = f"https://image.pollinations.ai/prompt/{msg}?width=512&height=512&seed={uuid.uuid4().hex[:4]}&nologo=true"
            return jsonify({"reply": f"Here is your image for: {msg}", "image": img_url, "download": img_url})

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are Nahata.AI, friendly AI that can edit photos, make logos, create PDFs, help with videos."},
                {"role": "user", "content": msg + uploaded_info}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(e)
        return jsonify({"reply": f"Error: {e}"}), 500

@app.route("/view-file/<name>")
def view_file(name):
    return send_file(f"uploads/{name}")

@app.route("/make-pdf", methods=["POST"])
def make_pdf():
    try:
        text = request.get_json().get("text","No content")
        file_id = uuid.uuid4().hex
        path = f"tmp/{file_id}.pdf"
        create_pdf(text, path)
        return jsonify({"pdf_url": f"/download-pdf/{file_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download-pdf/<file_id>")
def download_pdf(file_id):
    path = f"tmp/{file_id}.pdf"
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="NahataAI.pdf")
    return "File not found", 404

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    fid = uuid.uuid4().hex[:8]
    path = f"uploads/{fid}_{file.filename}"
    file.save(path)
    return jsonify({"url": f"/view-file/{fid}_{file.filename}", "name": file.filename})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
