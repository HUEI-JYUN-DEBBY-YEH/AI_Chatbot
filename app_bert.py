
from flask import Flask, request, render_template, session, redirect, url_for, jsonify
import os, json, torch
import openai
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
from datetime import datetime

# === 環境變數與 OpenAI Key ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, template_folder='template')
app.secret_key = 'secure_key'

# 使用者帳密（簡化測試用）
users = {"Debby": "123456"}

# === 載入模型與分類資料 ===
model_name = "DEBBY-YEH/finetuned-laborlaw-bert"
bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)

label2id = {
  "假別": 0, "其他": 1, "契約與聘僱關係": 2,
  "工時": 3, "終止與解僱": 4, "職場安全與性別平等": 5, "薪資": 6
}
id2label = {v: k for k, v in label2id.items()}

with open("classified_chunks_cleaned.json", "r", encoding="utf-8") as f:
    chunk_data = json.load(f)

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def predict_category(text):
    inputs = bert_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = bert_model(**inputs)
        predicted_id = torch.argmax(outputs.logits, dim=1).item()
        return id2label[predicted_id]

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
        chunks = chunk_data.get(predicted_label, [])[:3]

        if not chunks:
            return jsonify({"response": f"❌ 未找到分類 {predicted_label} 的資料。"})

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
        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ 錯誤：{e}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("verification"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Flask 準備啟動中...")
    app.run(host="0.0.0.0", port=port, debug=True)
