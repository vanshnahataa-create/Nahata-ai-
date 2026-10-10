from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from groq import Groq
import os
import uuid
import textwrap

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

os.makedirs("tmp", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# --- PERFECT PDF MAKER (No library needed) ---
def create_pdf(text, filepath):
    # Clean text for PDF
    text = text.replace("**","").replace("##","").replace("###","")

    # Wrap long lines
    wrapped_lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(textwrap.wrap(para, width=85, break_long_words=False) or [""])

    pages = []
    current_page_lines = []

    # 55 lines per page
    for line in wrapped_lines:
        current_page_lines.append(line)
        if len(current_page_lines) >= 55:
            pages.append(current_page_lines)
            current_page_lines = []
    if current_page_lines:
        pages.append(current_page_lines)

    if not pages:
        pages = [["No content"]]

    # Build PDF with multiple pages
    objects = []
    # Object 1: Catalog
    # Object 2: Pages
    # Object 3+: Page objects and contents will be added

    pdf_parts = []
    pdf_parts.append("%PDF-1.4\n")

    # Reserve positions
    # We will build from scratch with proper xref

    content_streams = []
    for page_lines in pages:
        stream = "BT\n/F1 12 Tf\n50 750 Td\n"
        for line in page_lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            safe = safe[:90]
            stream += f"({safe}) Tj\n0 -18 Td\n"
        stream += "ET"
        content_streams.append(stream)

    # Count objects: 1 Catalog, 2 Pages, 3 Font, 4..N Pages, then Contents
    # Let's build
    num_pages = len(pages)
    # Object numbers: 1=Catalog, 2=Pages, 3=Font, 4 to 3+num_pages = Page objects, then content objects

    obj_offsets = [0] # object 0

    # Obj 1
    obj1 = "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    obj_offsets.append(len("".join(pdf_parts)))
    pdf_parts.append(obj1)

    # Obj 2 - Pages with kids
    kids = " ".join([f"{4+i} 0 R" for i in range(num_pages)])
    obj2 = f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {num_pages} >> endobj\n"
    obj_offsets.append(len("".join(pdf_parts)))
    pdf_parts.append(obj2)

    # Obj 3 - Font
    obj3 = "3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    obj_offsets.append(len("".join(pdf_parts)))
    pdf_parts.append(obj3)

    # Page objects
    content_obj_start = 4 + num_pages
    for i in range(num_pages):
        page_obj_num = 4 + i
        content_obj_num = content_obj_start + i
        obj_page = f"{page_obj_num} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj_num} 0 R >> endobj\n"
        obj_offsets.append(len("".join(pdf_parts)))
        pdf_parts.append(obj_page)

    # Content objects
    for i, stream in enumerate(content_streams):
        content_obj_num = content_obj_start + i
        obj_content = f"{content_obj_num} 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
        obj_offsets.append(len("".join(pdf_parts)))
        pdf_parts.append(obj_content)

    # Xref
    xref_offset = len("".join(pdf_parts))
    pdf_parts.append(f"xref\n0 {len(obj_offsets)}\n")
    pdf_parts.append("0000000000 65535 f \n")
    for offset in obj_offsets[1:]:
        pdf_parts.append(f"{offset:010d} 00000 n \n")
    pdf_parts.append(f"trailer << /Size {len(obj_offsets)} /Root 1 0 R >>\n")
    pdf_parts.append(f"startxref\n{xref_offset}\n%%EOF")

    with open(filepath, "w", encoding="latin-1", errors="ignore") as f:
        f.write("".join(pdf_parts))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg = ""
        if request.content_type and 'multipart' in request.content_type:
            msg = request.form.get("message","")
        else:
            data = request.get_json(silent=True)
            msg = data.get("message","") if data else ""

        # File upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                fid = uuid.uuid4().hex[:6]
                save_name = f"{fid}_{file.filename}"
                file.save(f"uploads/{save_name}")
                if file.filename.lower().endswith(('.png','.jpg','.jpeg','.webp')):
                    return jsonify({"reply": f"Got your photo {file.filename}. What should I do? Edit background, make logo, enhance?", "image": f"/view-file/{save_name}"})

        if not msg:
            msg = "Hello"

        # Logo / Image generation
        if any(k in msg.lower() for k in ["logo", "make image", "generate image", "photo bana"]):
            img_url = f"https://image.pollinations.ai/prompt/{msg}?width=768&height=768&seed={uuid.uuid4().hex[:4]}&nologo=true"
            return jsonify({"reply": f"Generated for: {msg}", "image": img_url, "download": img_url})

        # Normal chat for question paper etc
        system_prompt = "You are Nahata.AI. When user asks for question paper, make proper formatted question paper with Q1, Q2, marks, sections. Use simple plain text, no markdown stars."

        resp = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg}
            ]
        )
        return jsonify({"reply": resp.choices[0].message.content})
    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": f"Error: {e}"}), 500

@app.route("/view-file/<name>")
def view_file(name):
    return send_file(f"uploads/{name}")

@app.route("/make-pdf", methods=["POST"])
def make_pdf():
    try:
        data = request.get_json()
        text = data.get("text","")
        if not text or len(text) < 5:
            return jsonify({"error": "No text found. First ask AI something."}), 400

        file_id = uuid.uuid4().hex
        path = f"tmp/{file_id}.pdf"
        create_pdf(text, path)
        return jsonify({"pdf_url": f"/download-pdf/{file_id}"})
    except Exception as e:
        print("PDF ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/download-pdf/<file_id>")
def download_pdf(file_id):
    path = f"tmp/{file_id}.pdf"
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="Nahata_Question_Paper.pdf")
    return "PDF not found, generate again", 404

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    fid = uuid.uuid4().hex[:6]
    path = f"uploads/{fid}_{file.filename}"
    file.save(path)
    return jsonify({"url": f"/view-file/{fid}_{file.filename}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
