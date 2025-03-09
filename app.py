from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import faiss
import numpy as np
import openai
from sentence_transformers import SentenceTransformer
from datetime import datetime
from dotenv import load_dotenv
import pickle

app = Flask(__name__, template_folder='template')
app.secret_key = 'asdfghjkl0987654321'  # 設定 session 安全密鑰

# 模擬身分驗證資料庫
users = {
    "David Chou": "A123456789",
    "Vivian Kuo": "B223348910",
    "Angela Tsai": "C221159139"
}

# 設定資料庫（Render 提供的 PostgreSQL 或本地 SQLite）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ✅ 載入 .env 檔案
load_dotenv()

# ✅ 讀取 OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("❌ 缺少 OPENAI_API_KEY，請確認 Render 環境變數設定！")

# ✅ 讀取環境變數
FAISS_DB_PATH = os.getenv("FAISS_DB_PATH", "/opt/render/project/src/Output_Vector")
TEXT_DATA_PATH = os.getenv("TEXT_DATA_PATH", "/opt/render/project/src/Output_Clean")
FAISS_INDEX_FILE = os.path.join(FAISS_DB_PATH, "vector_database.faiss")
PICKLE_FILE = os.path.join(FAISS_DB_PATH, "documents.pkl")

# ✅ 確保資料夾存在
os.makedirs(FAISS_DB_PATH, exist_ok=True)

# 讀取 Hugging Face Token
hf_token = os.getenv("HUGGINGFACE_TOKEN")

# 設定 cache folder 並下載模型
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-V2", 
    cache_folder="./model_cache", 
    use_auth_token=hf_token  # 使用 Hugging Face Token
)

# ✅ 讀取文本並建立向量索引
documents = []
document_vectors = []

if os.path.exists(TEXT_DATA_PATH):
    txt_files = sorted([f for f in os.listdir(TEXT_DATA_PATH) if f.endswith(".txt")])[:100]

    for filename in txt_files:
        file_path = os.path.join(TEXT_DATA_PATH, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read().strip()
            documents.append(text_content)
            document_vectors.append(embedding_model.encode(text_content))

# ✅ 確保 `document_vectors` 在 FAISS 初始化前已經有資料
if documents and document_vectors:
    #FAISS初始化
    d = 384  # 向量維度
    nlist = max(1, len(document_vectors) // 40)  # 讓 centroids 數量適應你的數據
    quantizer = faiss.IndexFlatL2(d)  # 量化器
    index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)
    
    index.train(np.array(document_vectors).astype(np.float32))  # ✅ 這裡才執行訓練
    index.add(np.array(document_vectors).astype(np.float32))  # ✅ 這裡新增資料
    faiss.write_index(index, FAISS_INDEX_FILE)  # ✅ 寫入索引
    
    # ✅ **儲存 `documents` 以便未來查找對應文本**
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(documents, f)

    print("✅ FAISS 資料庫已建立並儲存！")
    print(f"📁 Documents 長度: {len(documents)}")
else:
    print("❌ 錯誤：無法建立 FAISS，因為 `document_vectors` 為空！")


# ✅ 讀取 FAISS 資料庫
try:
    index = faiss.read_index(FAISS_INDEX_FILE)

    # ✅ 讀取 `documents`
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, "rb") as f:
            documents = pickle.load(f)
    
    print("✅ FAISS 資料庫成功載入！")
    print(f"📁 Documents 長度: {len(documents)}")
    print(f"📂 Documents 長度: {len(documents)}, 向量數量: {len(document_vectors)}")
except Exception as e:
    print(f"❌ FAISS 載入失敗: {e}")

# ✅ 定義 embedding 函數
def embed_text(text):
    return np.array([embedding_model.encode(text)]).astype(np.float32)

# ✅ 讓使用者驗證才能進入聊天
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
            session["username"] = username  # 設定 session
            return redirect(url_for("mainpage"))
        else:
            return render_template("verification.html", error="帳號或密碼錯誤，請重新輸入！")

    return render_template("verification.html")  # 顯示登入畫面

@app.route("/mainpage")
def mainpage():
    if "username" not in session:
        return redirect(url_for("verification"))
    return render_template("chatbot_mainpage.html")

# ✅ 聊天功能
@app.route("/api/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"error": "請先登入"}), 401

    try:
        data = request.get_json()
        user_input = data.get("message", "")
        print(f"使用者輸入: {user_input}")

        if not user_input:
            return jsonify({"response": "請輸入有效的問題"}), 400

        print("🔍 測試 FAISS 檢索...")
        user_embedding = embed_text(user_input)
        distances, indices = index.search(user_embedding, k=3)
        print("✅ FAISS 測試成功")
        print(f"📌 FAISS 搜尋結果 - 距離: {distances}, 索引: {indices}")

        retrieved_texts = []
        for idx in indices[0]:
            if 0 <= idx < len(documents):
                text = documents[idx][:300]  # ✅ 限制每個文本最多 300 字
                retrieved_texts.append(text)
            else:
                retrieved_texts.append(f"未知內容 (索引 {idx})")

        print(f"🔍 FAISS 搜索結果：{retrieved_texts}")

        if all("未知內容" in text for text in retrieved_texts):
            return jsonify({"error": "❌ FAISS 搜索無效，請確認索引庫內容"}), 500

        print("📝 呼叫 OpenAI API 中...")
        prompt = f"""
        你是一個 AI 助手，請根據 FAISS 提供的背景資訊回答問題。
        背景資料：{retrieved_texts}
        問題：{user_input}
        """
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "請提供回答"},
            ],
            temperature=0,
            max_tokens=150,
            stop=["\n\n"]  # ✅ 讓回應在雙換行時結束
        )

        answer = response.choices[0].message.content
        print(f"💬 OpenAI 回應: {answer}")

        # ✅ 儲存對話到資料庫
        chat_record = ChatHistory(
            username=session["username"],
            user_message=user_input,
            bot_response=answer
        )
        db.session.add(chat_record)
        db.session.commit()

        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ FAISS 測試失敗: {e}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

# ✅ 對話歷史紀錄
@app.route("/api/history", methods=["GET"])
def history():
    if "username" not in session:
        return jsonify({"error": "請先登入"}), 401

    records = ChatHistory.query.filter_by(username=session["username"]).all()
    return jsonify([
        {"user_message": r.user_message, "bot_response": r.bot_response, "timestamp": r.timestamp}
        for r in records
    ])

# ✅ 設定 ChatHistory 資料表
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render 會自動提供 PORT
    app.run(host="0.0.0.0", port=port, debug=True)
