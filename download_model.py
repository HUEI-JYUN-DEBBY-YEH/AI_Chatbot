import os
from huggingface_hub import snapshot_download

def download_finetuned_model():
    model_dir = "./finetuned_laborlaw_model"
    
    if not os.path.exists(model_dir):
        print("📥 正在從 Hugging Face 下載 BERT fine-tuned 模型...")
        snapshot_download(
            repo_id="DEBBY-YEH/finetuned-laborlaw-bert",
            local_dir=model_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
    else:
        print("✅ 模型資料夾已存在，略過下載")

    # ✅ 檢查模型檔案是否存在
    model_path = os.path.join(model_dir, "model.safetensors")
    if not os.path.exists(model_path):
        raise FileNotFoundError("❌ 無法找到 model.safetensors，請確認 Hugging Face 上傳完成且檔名正確！")
    else:
        print("✅ 成功找到 model.safetensors，模型準備完畢！")
