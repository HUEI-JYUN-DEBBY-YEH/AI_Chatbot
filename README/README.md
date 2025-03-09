 🤖 AI Chatbot Project
🚀 這是一個基於 Flask + FAISS + OpenAI API 的 AI 聊天機器人，可自動檢索資料並回答問題

📌 功能特色
- 🔍 基於 FAISS 向量數據庫的檢索
- 🏗  與 OpenAI API 整合進行對話
- 📊 儲存並檢索對話歷史
- 🌐 可部署至 Render

📚 技術架構
- 後端：Flask + SQLite + FAISS + OpenAI API
- 前端：HTML + CSS + Bootstrap
- 向量模型：`sentence-transformers/all-MiniLM-L6-V2`
- 資料庫：SQLAlchemy（支援 PostgreSQL / SQLite）

🚀 快速開始
```bash
git clone https://github.com/你的帳號/AI_Chatbot_Project.git
cd AI_Chatbot_Project
pip install -r requirements.txt
python app.py

🔥未來擴展
✅ 改進回應的準確度
✅ 增加多語言支持
✅ 支援 PDF / Word 文本處理