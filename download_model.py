import os
from huggingface_hub import snapshot_download

def download_finetuned_model():
    model_dir = "./finetuned_laborlaw_model"
    if not os.path.exists(model_dir):
        print("📥 正在下載 BERT fine-tuned 模型...")
        snapshot_download(
            repo_id="DEBBY-YEH/finetuned-laborlaw-bert",  # 👈 填入妳的 repo_id
            local_dir=model_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
    else:
        print("✅ 模型已存在，跳過下載")
