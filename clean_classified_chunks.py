# clean_classified_chunks.py
# 將 classified_chunks.json 中的 "nan" 分類移除，輸出乾淨版

import json

# === 檔案路徑設定 ===
input_file = "classified_chunks.json"
output_file = "classified_chunks_cleaned.json"

# === 載入 JSON ===
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# === 清除分類為 nan 的內容 ===
cleaned_data = {label: chunks for label, chunks in data.items() if label.lower() != "nan"}

# === 儲存清理後的版本 ===
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

print(f"✅ 已完成清理，儲存為：{output_file}")
