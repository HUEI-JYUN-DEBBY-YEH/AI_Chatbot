from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import faiss
import numpy as np
import openai
from sentence_transformers import SentenceTransformer
from datetime import datetime
from dotenv import load_dotenv

app = Flask (__name__) 
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


@app.route('/')
def home():
    return redirect(url_for('verification')) #預設導向驗證頁面

@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
    
        if username in users and users[username]==password:
            session['username']=username  #設定session，表示登入成功
            return redirect(url_for('mainpage'))
        else:
            return render_template('verification.html', error="帳號或密碼錯誤，請重新輸入！")

    return render_template('verification.html')


@app.route('/mainpage')
def mainpage():
    if 'username' not in session:
        return redirect(url_for('verification'))  # 如果未登入，導回驗證頁面
    return render_template('chatbot_mainpage.html')  # ✅ 進入聊天頁面


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

        # ✅ 這裡加上限制前 2 條文本
        retrieved_texts = retrieved_texts[:2]

        prompt = f"使用者問題: {user_input}\n\n相關背景資料:\n{retrieved_texts[:500]}\n\n請根據以上內容回答:"

        # ✅ 改用新的 OpenAI API 語法
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content  # ✅ 正確取得回答內容

        return jsonify({"response": answer})

    except Exception as e:
        print(f"❌ 伺服器錯誤: {str(e)}")  # ✅ 讓 Flask 終端機顯示錯誤訊息
        return jsonify({"error": "伺服器發生錯誤，請稍後再試"}), 500


@app.route('/logout')
def logout():
    session.pop('username', None)  #清除session
    return redirect(url_for('verification'))  #登出後導回驗證頁面

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# 確保資料表建立
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)