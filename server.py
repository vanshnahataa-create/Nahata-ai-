from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
import os

app = Flask(__name__)
CORS(app)

# This will read key from Render Environment Variable
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    api_key = "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" # paste here as backup

client = Groq(api_key=api_key)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        if not user_msg:
            return jsonify({"reply": "Please type something"})

        response = client.chat.completions.create(
            model="llama-3.1-8b-versatile",
            messages=[
                {"role": "system", "content": "You are Nahata.AI, made by Nahata family from Chandvad."},
                {"role": "user", "content": user_msg}
            ]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print(f"ERROR: {e}") # This will show in Render Logs
        return jsonify({"reply": f"Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
