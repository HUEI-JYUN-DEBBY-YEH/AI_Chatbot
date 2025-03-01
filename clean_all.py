import os
import pandas as pd
import fitz  # pymupdf
from docx import Document

#設定原始資料夾與輸出資料夾
input_folder="YOUR_INPUT_FOLDER" #存放原始的PDF、Word、Excel檔案 
output_folder="YOUR_OUTPUT_FOLDER"  #存放清理後的檔案

if not os.path.exists(output_folder):
    os.makedirs(output_folder)  #如果輸出資料夾不存在，就建立它

#處理Excel檔案
def process_excel(file_path, output_path):
    df=pd.read_excel(file_path)

    #清理資料:刪除空值&重複值
    df=df.dropna().drop_duplicates()

    #儲存清理後的Excel
    output_file=os.path.join(output_path, os.path.basename(file_path))
    df.to_excel(output_file, index=False)
    print(f"清理後的Excel已儲存: {output_file}")


#處理Word檔案
def process_word(file_path,output_path):
    doc=Document(file_path)

    #讀取所有文字段落
    text="\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    #儲存清理後的Word內容為txt檔案
    output_file=os.path.join(output_path, os.path.basename(file_path).replace(".docx", ".txt"))
    with open(output_file, "w", encoding='utf-8") as f:
        f.write(text)
    print(f"清理後的Word內容已儲存: {output_file}")


#處理PDF檔案
def process_pdf(file_path, output_path):
    doc=fitz.open(file_path)
    text=""

    #讀取每一頁的文字
    for page in doc:
        text += page.get_text("text")+"\n"
    
    #儲存清理後的PDF內容為txt檔案
    output_file=os.path.join(output_path, os.path.basename(file_path).replace(".pdf", ".txt"))
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"清理後的PDF內容已儲存: {output_file}")


#讀取資料夾內所有檔案
for filename in os.listdir(input_folder):
    file_path=os.path.join(input_folder, filename)

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        process_excel(file_path, output_folder)
    
    elif filename.endswith(".docx"):
        process_word(file_path, output_folder)

    elif filename.endswith(".pdf"):
        process_pdf(file_path, output_folder)

print("所有檔案處理完成！")