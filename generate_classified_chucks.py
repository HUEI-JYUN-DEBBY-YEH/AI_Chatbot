# generate_classified_chunks.py
# 將標註資料依照 label 分群成 {label: [text1, text2, ...]} 結構

import pandas as pd
import json
import os

# === 檔案路徑設定 ===
input_file = "laborlaw_sentences_labeled.csv"  # <-- 請改成妳的原始檔名（支援 .csv 或 .json）
output_file = "classified_chunks.json"

# === 讀取資料 ===
if input_file.endswith(".csv"):
    df = pd.read_csv(input_file)
elif input_file.endswith(".json"):
    df = pd.read_json(input_file)
else:
    raise ValueError("❌ 不支援的檔案格式，請使用 .csv 或 .json")

# === 確認必要欄位 ===
if "text" not in df.columns or "label" not in df.columns:
    raise ValueError("❌ 檔案中需要包含 'text' 與 'label' 欄位")

# === 分群 ===
classified = {}
for _, row in df.iterrows():
    label = str(row["label"]).strip()
    text = str(row["text"]).strip()
    if label and text:
        classified.setdefault(label, []).append(text)

# === 儲存成 JSON ===
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(classified, f, ensure_ascii=False, indent=2)

print(f"✅ 已成功產出分類 chunks 檔案：{output_file}")
