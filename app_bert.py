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

# === 載入環境變數與 OpenAI Key ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === 初始化 Flask ===
app = Flask(__name__, template_folder='template')
app.secret_key = 'asdfghjkl123456789'

# === 使用者帳密（範例） ===
users = {"David Chou": "A123456789"}

# === 資料庫設定 ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
db = SQLAlchemy(app)

# === ChatHistory模型 ===
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# === ✅ 載入 BERT fine-tuned 模型 ===
model_name = "DEBBY-YEH/finetuned-laborlaw-bert"
bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
label2id = {'特休': 0, '工會': 1, '勞動契約': 2, '工時': 3, '職災': 4, '派遣': 5, '產假育嬰': 6, '工資': 7, '職場歧視': 8}
id2label = {v: k for k, v in label2id.items()}

# === ✅ 載入向量模型（可省略 GPT 調用）===
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# === ✅ 首頁 ===
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

# === ✅ 問答主邏輯 ===
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

# === ✅ 提供歷史 API（for JSON下載）===
@app.route("/api/history", methods=["GET"])
def get_history():
    username = session.get("username", "Guest")
    history = ChatHistory.query.filter_by(username=username).order_by(ChatHistory.timestamp).all()
    result = [{"question": h.question, "answer": h.answer, "timestamp": h.timestamp.isoformat()} for h in history]
    return jsonify(result)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("verification"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Flask 準備啟動中...")
    app.run(host="0.0.0.0", port=port, debug=True)
