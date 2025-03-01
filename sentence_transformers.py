import os
from sentence_transformers import SentenceTransformer

input_folder="YOUR_INPUT_FOLDER"
output_folder="YOUR_OUTPUT_FOLDER"

if not os.path.exists(output_folder):
    os.makedirs("output_folder")

def process_file(file_path, output_path)
for file in file_list():
    model = SentenceTransformer()
    document_embeddings = model.encode()

query = ""
query_embedding = model.encode(query)

output_file=os.path.join(output_path, os.path.basename(file_path).replace(".*", ".faiss"))
print(f"資料已轉換成向量資料庫FAISS格式: {output_file}")