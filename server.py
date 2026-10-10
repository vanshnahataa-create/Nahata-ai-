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
    parts=["%PDF-1.4\n"]
    offsets=[0]
    offsets.append(len("".join(parts)))
    parts.append
