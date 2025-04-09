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
class BERTChatHistory(db.Model):
    __tablename__ = 'bert_chat_history'  # ✅ 使用不同表名

    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text)
    bert_label = db.Column(db.String(50))
    gpt_response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# === ✅ 載入 BERT fine-tuned 模型 ===
model_name = "DEBBY-YEH/finetuned-laborlaw-bert"
bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)

# ✅ label 對應
label2id = {
  "假別": 0,
  "其他": 1,
  "契約與聘僱關係": 2,
  "工時": 3,
  "終止與解僱": 4,
  "職場安全與性別平等": 5,
  "薪資": 6
}
id2label = {v: k for k, v in label2id.items()}

# === ✅ 載入 chunks（分類好的資料）===
try:
    with open("classified_chunks_cleaned.json", "r", encoding="utf-8") as f:
        chunk_data = json.load(f)
    print(f"✅ 已成功讀取分類檔，共有 {len(chunk_data)} 類分類。")
except Exception as e:
    print(f"❌ 無法讀取 classified_chunks_cleaned.json：{e}")

# ✅ 分類函式
def predict_category(text):
    inputs = bert_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = bert_model(**inputs)
        predicted_id = torch.argmax(outputs.logits, dim=1).item()
        return id2label[predicted_id]

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
            answer = f"❌ 未找到分類 {predicted_label} 的資料。"
            new_record = BERTChatHistory(
                user_input=user_input,
                bert_label=predicted_label,
                gpt_response=answer
            )
            db.session.add(new_record)
            db.session.commit()
            return jsonify({"response": answer})

        print(f"📌 BERT 分類結果：{predicted_label}")

        prompt = f"""
        你是一位熟悉台灣勞基法的法律助理，請根據下列背景資料回答使用者問題：
        背景資料：{chunks}
        問題：{user_input}
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "請根據上面內容回答問題"},
            ],
            temperature=0,
            max_tokens=200
        )

        answer = response.choices[0].message["content"]

        new_record = BERTChatHistory(
            user_input=user_input,
            bert_label=predicted_label,
            gpt_response=answer
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ BERT-GPT 錯誤：{e}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

# === ✅ 提供歷史 API（for JSON下載）===
@app.route("/api/history", methods=["GET"])
def get_history():
    username = session.get("username", "Guest")
    history = BERTChatHistory.query.order_by(BERTChatHistory.timestamp).all()
    result = [
        {
            "question": h.user_input,
            "category": h.bert_label,
            "answer": h.gpt_response,
            "timestamp": h.timestamp.isoformat()
        }
        for h in history
    ]
    return Response(json.dumps(result, ensure_ascii=False), mimetype='application/json')

with app.app_context():
    count = BERTChatHistory.query.count()
    print(f"✅ PostgreSQL 已連線，紀錄數量：{count}")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("verification"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Flask 準備啟動中...")
    app.run(host="0.0.0.0", port=port, debug=True)
