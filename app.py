from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import faiss
import numpy as np
import openai
from sentence_transformers import SentenceTransformer
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__, template_folder='template')
app.secret_key='asdfghjkl0987654321' #設定session安全密鑰

#模擬身分驗證資料庫
users={
    "David Chou": "A123456789", 
    "Vivian Kuo": "B223348910", 
    "Angela Tsai": "C221159139"
    }

# 設定 Render 提供的 DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")  # 預設本地 SQLite 以防止環境變數遺失
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ✅ 載入 .env 檔案
load_dotenv()

# ✅ 讀取 OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("❌ 缺少 OPENAI_API_KEY，請確認Render環境變數設定！")

# ✅ 讀取環境變數
FAISS_DB_PATH = os.getenv("FAISS_DB_PATH", "C:\\Users\\USER\\OneDrive\\Github\\1. AI ChatBot\\Output_Vector")
TEXT_DATA_PATH = os.getenv("TEXT_DATA_PATH", "C:\\Users\\USER\\OneDrive\\Github\\1. AI ChatBot\\Output_Clean")
FAISS_INDEX_FILE = os.path.join(FAISS_DB_PATH, "vector_database.faiss")

# ✅ 確保資料夾存在
os.makedirs(FAISS_DB_PATH, exist_ok=True)

# ✅ 初始化模型
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-V2", cache_folder="./model_cache")

# ✅ 讀取文本並建立向量索引
documents = []
document_vectors = []

if os.path.exists(TEXT_DATA_PATH):
    txt_files = sorted([f for f in os.listdir(TEXT_DATA_PATH) if f.endswith(".txt")])

    for filename in txt_files:
        file_path = os.path.join(TEXT_DATA_PATH, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read().strip()
            documents.append(text_content)
            document_vectors.append(embedding_model.encode(text_content))

# ✅ 檢查 FAISS 是否已經存在
if not os.path.exists(FAISS_INDEX_FILE):
    print("⚠️ 找不到 FAISS 資料庫，正在建立新的 FAISS 索引！")
    
    # ✅ 確保 documents 內有資料
    if documents:
        index = faiss.IndexFlatL2(384)  # 假設向量維度 384
        index.add(np.array(document_vectors))  # ✅ 新增向量到索引
        faiss.write_index(index, FAISS_INDEX_FILE)
        print("✅ FAISS 資料庫已建立並儲存！")
    else:
        print("❌ 錯誤：無法建立 FAISS，因為 `Output_Clean` 內沒有文本檔案！")

# ✅ 讀取 FAISS 資料庫
try:
    index = faiss.read_index(FAISS_INDEX_FILE)
    print("✅ FAISS 資料庫成功載入！")
except Exception as e:
    print(f"❌ FAISS 載入失敗: {e}")

# ✅ 確保 OpenAI API Key 存在
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ 缺少 OPENAI_API_KEY，請確認 Render 環境變數設定！")

client = openai.OpenAI(api_key=api_key)  # ✅ 確保 API Key 正確設定
print("✅ OpenAI API 連線成功！")

# ✅ 初始化 SentenceTransformer 模型
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-V2",
    cache_folder="./model_cache"
)
print("✅ LLM 模型下載完成，準備運行應用...")

# ✅ 定義 embedding 函數，確保輸出格式符合 FAISS 要求
def embed_text(text):
    embedding = embedding_model.encode(text)
    return np.array(embedding).reshape(1, -1)  # ✅ 確保 shape 為 (1, 384)

@app.route("/health")
def health():
    """提供 Render 監測服務運行狀態"""
    return "OK", 200

@app.route("/")
def home():
    """首頁：Render 需要時回應 AI Chatbot 狀態，否則導向驗證"""
    if os.environ.get("RENDER_ENV") == "production":
        return "AI Chatbot is running!"
    return redirect(url_for('verification'))  # 預設導向驗證頁面

@app.route("/verification", methods=["GET", "POST"])
def verification():
    """登入驗證邏輯"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users.get(username) == password:  # 用 `get()` 避免 KeyError
            session["username"] = username  # 設定 session
            return redirect(url_for("mainpage"))
        else:
            return render_template("verification.html", error="帳號或密碼錯誤，請重新輸入！")

    return render_template("verification.html")  # 預設顯示登入畫面

@app.route("/mainpage")
def mainpage():
    """主頁面：只有通過驗證的用戶才能進入"""
    if "username" not in session:
        return redirect(url_for("verification"))  # 未登入則返回驗證頁面
    return render_template("chatbot_mainpage.html")  # 進入聊天頁面


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        # 先測試 FAISS 是否可用
        test_query = "測試"
        user_embedding = embed_text(test_query).reshape(1, -1) #確保是(1, 384)
        distances, indices = index.search(user_embedding, k=3)
        
        retrieved_texts = []
        for idx in indices[0]:
            if 0 <= idx < len(documents):
                retrieved_texts.append(documents[idx])
            else:
                retrieved_texts.append(f"未知內容 (索引 {idx})")
        
        print(f"🔍 FAISS 測試結果：{retrieved_texts}")  # 在 Log 內顯示 FAISS 內容
        
        if all("未知內容" in text for text in retrieved_texts):
            return jsonify({"error": "❌ FAISS 搜索無效，請確認索引庫內容"}), 500

        # 繼續處理 AI 聊天
        data = request.get_json()
        user_input = data.get("message", "")

        if not user_input:
            return jsonify({"response": "請輸入有效的問題"}), 400

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
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ FAISS 測試失敗: {e}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

@app.route('/logout')
def logout():
    session.pop('username', None)  #清除session
    return redirect(url_for('verification'))  #登出後導回驗證頁面

@app.route("/api/history", methods=["GET"])
def history():
    return {"message": "This is the history API!"}

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# 確保資料表建立
with app.app_context():
    db.create_all()

# 確保 Flask 監聽 Render 指定的 PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # 預設 10000，Render 會自動設定 PORT 環境變數
    app.run(host="0.0.0.0", port=port, debug=True)