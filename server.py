from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
from fpdf import FPDF
import os
import requests
import uuid

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("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"))

# Create temp folder
os.makedirs("tmp", exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message","")

        # If user asks for logo/image - generate image
        if "logo" in msg.lower() or "image" in msg.lower() or "photo" in msg.lower():
            prompt = msg.replace("make","").replace("logo","").strip()
            # Free image API - no key needed
            img_url = f"https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&seed={uuid.uuid4().hex[:4]}&nologo=true"
            return jsonify({"reply": f"Here is your logo for: {prompt}", "image": img_url, "download": img_url})

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are Nahata.AI, made by Nahata family. Helpful and friendly."},
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
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        # Handle unicode
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, safe_text)
        file_id = uuid.uuid4().hex
        path = f"tmp/{file_id}.pdf"
        pdf.output(path)
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
