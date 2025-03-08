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
DATABASE_URL = os.getenv("postgresql://chatbot_aihr_user:5qlSd9DnQ4Qsg1VlkLYUJdYzFi8CkRAH@dpg-cv3dcn3tq21c73bjp2r0-a/chatbot_aihr", "sqlite:///test.db")  # 預設本地 SQLite 以防止環境變數遺失
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ✅ 載入 .env 檔案
load_dotenv()

# ✅ 讀取 OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("❌ 缺少 OPENAI_API_KEY，請確認Render環境變數設定！")

db_folder = "Output_Vector"
db_path = os.path.join(db_folder, "vector_database.faiss")

# 確保資料夾存在
os.makedirs(db_folder, exist_ok=True)

# 如果檔案不存在，自動建立一個 FAISS 資料庫
if not os.path.exists(db_path):
    print("⚠️ 找不到 FAISS 資料庫，正在建立新的 FAISS 索引！")
    index = faiss.IndexFlatL2(384)  # 假設向量維度為 384
    faiss.write_index(index, db_path)
    print("✅ FAISS 資料庫已建立！")

# 讀取 FAISS 索引
index = faiss.read_index(db_path)
print("✅ FAISS 資料庫載入成功！")

documents = []
vector_data_folder = "C:/Users/USER/OneDrive/Github/1. AI ChatBot/Output_Clean"

if os.path.exists(vector_data_folder):  # 確保資料夾存在
    for filename in sorted(os.listdir(vector_data_folder)):  
        if filename.endswith(".txt"):
            file_path = os.path.join(vector_data_folder, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                documents.append(f.read().strip())  # 讀取並去除空白   

if not documents:  
    print("⚠️ 警告：`documents` 為空，請確認 `Output_Clean` 資料夾內有 `.txt` 檔案！")


#初始化LLM(OpenAI GPT API)
openai.api_key=os.getenv("OPENAI_API_KEY")   #從環境變數讀取API Key
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-V2", cache_folder="./model_cache")
print("模型下載完成，準備運行應用...")


@app.route("/health")
def health():
    """提供 Render 監測服務運行狀態"""
    return "OK", 200

@app.route('/test_faiss', methods=['GET'])
def test_faiss():
    try:
        FAISS_DB_PATH = os.getenv("FAISS_DB_PATH", "/opt/render/project/src/Output_Vector/vector_database.faiss")
        
        if not os.path.exists(FAISS_DB_PATH):
            return jsonify({"error": "❌ 找不到 FAISS 資料庫，請確認檔案是否存在！"}), 500

        import faiss
        import numpy as np

        index = faiss.read_index(FAISS_DB_PATH)
        D = index.d  # 取得 FAISS index 的維度
        user_embedding = np.random.rand(1, D).astype("float32")

        k = 3
        distances, indices = index.search(user_embedding, k)

        return jsonify({
            "message": "✅ FAISS 測試成功！",
            "indices": indices.tolist(),
            "distances": distances.tolist()
        })

    except Exception as e:
        return jsonify({"error": f"❌ FAISS 測試失敗: {str(e)}"}), 500


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


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'username' not in session:
            return jsonify({"error": "未登入，請先驗證身分"}), 401

        user_input = request.json.get("message", "")

        if not user_input:
            return jsonify({"error": "請輸入訊息"}), 400

        # 轉換使用者輸入為向量
        user_embedding = model.encode([user_input])
        user_embedding = np.array(user_embedding, dtype=np.float32)

        # 在 FAISS 中尋找最相關的文本
        k = 3
        distances, indices = index.search(user_embedding, k)

        retrieved_texts = []
        for idx in indices[0]:  
            if 0 <= idx < len(documents):  
                retrieved_texts.append(documents[idx])
            else:
                retrieved_texts.append(f"未知內容 (索引 {idx})")
        print(f"🔍 FAISS 提供的背景資料:\n{retrieved_texts}")

        # ✅ 這裡加上限制最多取3 條資料，並限制總長度
        MAX_TOKENS = 1000 
        merged_texts = " ".join(retrieved_texts[:3])[:500]  # 取最多 2個文檔 & 限制 500 tokens
        merged_texts = merged_texts[:merged_texts.rfind(" ")]  # 確保不截斷單詞

        #設計Prompt，確保AI聚焦在FAISS檢索道的資料
        prompt = f"""
        你是一個專業 AI 助手，請根據提供的FAISS背景資料回答問題。  
        如果背景資料不足，你可以根據你的知識做簡要回答。  
        但請保持回應清晰、具體，並確保邏輯正確。 

        🔍 **背景資料**
        {retrieved_texts}

        ❓ **問題**
        {user_input}
        """

        # ✅ 使用OpenAI API 進行回應
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try: 
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "請提出問題"},
                ],
                temperature=0,  # 📌 降低隨機性，讓回答更準確
                max_tokens=300,  # 避免回應過長
                stop=["\n\n"]
            )
            answer = response.choices[0].message.content  # ✅ 正確取得回答內容
            print(f"🤖 AI 回應: {answer}")
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            answer = "對不起，我無法處理您的請求。"
        
        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ 伺服器錯誤: {str(e)}")  # ✅ 讓 Flask 終端機顯示錯誤訊息
        return jsonify({"error": "伺服器發生錯誤，請稍後再試"}), 500


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