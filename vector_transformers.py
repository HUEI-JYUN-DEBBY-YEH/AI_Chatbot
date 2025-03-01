import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

input_folder="YOUR_INPUT_FOLDER"
output_folder="YOUR_OUTPUT_FOLDER"
if not os.path.exists(output_folder):
    os.makedirs(output_folder, exist_ok=True)
output_file=os.path.join(output_folder, "vector_database.faiss")


#定義FAISS儲存路徑
faiss_output_file=os.path.join(output_folder, "vector_database.faiss")


#初始化SentenceTransformer模型
model=SentenceTransformer("all-MiniLM-L6-V2")  #一個小而快的NLP模型

#建立FAISS向量資料庫
dimension=384  #'all-MiniLM-L6-V2'輸出的向量維度
index=faiss.IndexFlatL2(dimension)  #L2距離索引

#處理所有.txt檔案
def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text=f.read().strip() #讀取文本並去除首尾空白

    if not text:
        print(f"檔案{file_path}為空，跳過處理。")
        return
    
    #轉換為向量
    document_embedding=model.encode([text])  #轉成數值向量
    document_embedding=np.array(document_embedding, dtype=np.float32)  #FAISS需要Float32

    #加入FAISS向量資料庫
    index.add(document_embedding)

    print(f"轉換成功:{file_path}")

#遍歷所有.txt檔案
for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        file_path=os.path.join(input_folder, filename)
        process_file(file_path)


#確保FAISS可以寫入檔案
try:
    faiss.write_index(index, faiss_output_file)
    print(f"向量資料庫已儲存至:{faiss_output_file}")
except Exception as e:
    print(f"儲存FAISS向量資料庫時發生錯誤: {e}")