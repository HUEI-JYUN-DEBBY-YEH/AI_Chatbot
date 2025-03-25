import os
import requests

def download_finetuned_model():
    model_dir = "./finetuned_laborlaw_model"
    os.makedirs(model_dir, exist_ok=True)

    # ✅ Hugging Face 靜態下載連結
    model_url = "https://huggingface.co/DEBBY-YEH/finetuned-laborlaw-bert/resolve/main/model.safetensors"
    save_path = os.path.join(model_dir, "model.safetensors")

    if os.path.exists(save_path):
        print("✅ model.safetensors 已存在，略過下載")
        return

    print("📥 正在從 Hugging Face 下載 model.safetensors...")

    # ⚠️ 下載模型檔
    response = requests.get(model_url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ model.safetensors 下載完成")
    else:
        raise RuntimeError(f"❌ 下載失敗，HTTP 狀態碼: {response.status_code}")
