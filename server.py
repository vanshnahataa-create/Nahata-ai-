from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
import os
import uuid

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

os.makedirs("tmp", exist_ok=True)

# SIMPLE PDF MAKER - NO LIBRARY NEEDED
def create_pdf(text, filepath):
    # Escape PDF text
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    # Split into lines
    lines = safe.split("\n")
    stream = "BT\n/F1 12 Tf\n50 750 Td\n"
    for line in lines[:60]: # max 60 lines per page
        if not line.strip():
            stream += "0 -18 Td\n"
            continue
        # limit length
        line = line[:90]
        stream += f"({line}) Tj\n0 -18 Td\n"
    stream += "ET"

    # Build PDF objects
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
        data = request.get_json()
        msg = data.get("message","")
        if "logo" in msg.lower() or "image" in msg.lower() or "photo" in msg.lower():
            prompt = msg
            img_url = f"https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&seed={uuid.uuid4().hex[:4]}&nologo=true"
            return jsonify({"reply": f"Here is your logo for: {prompt}", "image": img_url, "download": img_url})

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are Nahata.AI, made by Nahata family."},
                {"role": "user", "content": msg}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(e)
        return jsonify({"reply": f"Error: {e}"}), 500

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
