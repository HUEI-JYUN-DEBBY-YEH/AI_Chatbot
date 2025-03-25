import json
import pandas as pd
import os

json_path = "baseline_gpt_faiss_check_history.json"
csv_output_path = "gpt_faiss_answers_for_labeling.csv"

# 確認路徑是否正確
if not os.path.exists(json_path):
    print(f"❌ 找不到 JSON 檔案：{json_path}")
    exit()

# 讀檔 + 寫檔
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

records = [
    {"question": d["question"], "answer_gpt": d["answer"], "is_correct": ""}
    for d in data
]

df = pd.DataFrame(records)

try:
    df.to_csv(csv_output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 成功轉檔，CSV 儲存於：{csv_output_path}")
except Exception as e:
    print(f"❌ 儲存失敗：{e}")
