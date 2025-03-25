# app_bert.py
# ✅ 加入 BERT 分類器，根據 user_input 選擇類別對應 chunks 做 GPT 回答

from flask import Flask, request, render_template, session, redirect, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os, pickle, json, torch
import numpy as np
import openai
from dotenv import load_dotenv
from datetime import datetime
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# === 初始化 Flask ===
app = Flask(__name__, template_folder='template')
app.secret_key = 'asdfghjkl123456789'

# === 使用者帳密（範例） ===
users = {"David Chou": "A123456789"}

# === 載入環境變數與 OpenAI Key ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === 資料庫設定 ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# === 建立 DB ===
db = SQLAlchemy(app)
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# === 模型與資料路徑 ===
label2id = json.load(open("label2id.json", encoding="utf-8"))
id2label = {v: k for k, v in label2id.items()}
tokenizer = AutoTokenizer.from_pretrained("finetuned_laborlaw_model")
model = AutoModelForSequenceClassification.from_pretrained("finetuned_laborlaw_model")
model.eval()

with open("classified_chunks_cleaned.json", "r", encoding="utf-8") as f:
    chunk_data = json.load(f)

embedding_model = SentenceTransformer("./embedding_model")

def predict_category(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
        pred_id = torch.argmax(logits, dim=1).item()
    return id2label[pred_id]

@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("verification"))
    return redirect(url_for("mainpage"))

@app.route("/verification", methods=["GET", "POST"])
def verification():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if users.get(username) == password:
            session["username"] = username
            return redirect(url_for("mainpage"))
        else:
            return render_template("verification.html", error="帳號或密碼錯誤")
    return render_template("verification.html")

@app.route("/mainpage")
def mainpage():
    if "username" not in session:
        return redirect(url_for("verification"))
    return render_template("chatbot_mainpage.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"error": "請先登入"}), 401

    data = request.get_json()
    user_input = data.get("message", "")
    if not user_input:
        return jsonify({"response": "請輸入問題"}), 400

    try:
        predicted_label = predict_category(user_input)
        chunks = chunk_data.get(predicted_label, [])[:3]  # 取前3筆分類內 chunk
        if not chunks:
            return jsonify({"response": f"❌ 未找到分類 {predicted_label} 的資料。"})

        print(f"📌 BERT 分類結果：{predicted_label}")

        prompt = f"""
        你是一個 AI 助手，請根據以下背景資料回答問題：
        背景資料：{chunks}
        問題：{user_input}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "請提供回答"},
            ],
            temperature=0,
            max_tokens=150,
            stop=["\n\n"]
        )
        answer = response.choices[0].message["content"]

        chat_record = ChatHistory(
            username=session["username"],
            user_message=user_input,
            bot_response=answer
        )
        db.session.add(chat_record)
        db.session.commit()

        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ BERT-GPT 模式失敗：{e}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

@app.route("/api/history", methods=["GET"])
def history():
    if "username" not in session:
        return jsonify({"error": "請先登入"}), 401
    records = ChatHistory.query.filter_by(username=session["username"]).all()
    history_data = [
        {
            "user": r.username,
            "question": r.user_message,
            "answer": r.bot_response,
            "timestamp": r.timestamp
        }
        for r in records
    ]
    return Response(json.dumps(history_data, ensure_ascii=False), content_type="application/json; charset=utf-8")

@app.route("/api/check_history", methods=["GET"])
def check_history():
    records = ChatHistory.query.all()
    history_data = [
        {
            "user": r.username,
            "question": r.user_message,
            "answer": r.bot_response,
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in records
    ]
    return Response(json.dumps(history_data, ensure_ascii=False), content_type="application/json; charset=utf-8")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Flask 準備啟動中...")
    app.run(host="0.0.0.0", port=port, debug=True)
