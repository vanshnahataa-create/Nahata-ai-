from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("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"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message","")

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b", # <-- NEW MODEL 100% WORKING
            messages=[
                {"role": "system", "content": "You are Nahata.AI, made by Nahata family."},
                {"role": "user", "content": msg}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(e)
        return jsonify({"reply": f"Server Error: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
