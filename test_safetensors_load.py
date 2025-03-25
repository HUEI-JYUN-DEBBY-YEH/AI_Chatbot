from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 嘗試載入 safetensors 格式的模型
print("🚀 嘗試載入 BERT 分類器...")
model_path = "finetuned_laborlaw_model"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

print("✅ 分類模型與 tokenizer 載入成功！")
