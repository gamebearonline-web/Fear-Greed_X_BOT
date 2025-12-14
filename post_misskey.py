# ==========================================
# post_misskey.py（スプラ方式・投稿文対応版）
# ==========================================
import os
import requests

MISSKEY_HOST  = os.getenv("MISSKEY_HOST")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")

IMAGE_PATH     = os.getenv("IMAGE_PATH", "fgi-image/FearGreed_Output.png")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH", "fgi-image/post_text.txt")

# -------------------------------
# バリデーション
# -------------------------------
if not MISSKEY_HOST or not MISSKEY_TOKEN:
    raise Exception("[ERROR] Misskey 環境変数が不足しています")

if not os.path.exists(IMAGE_PATH):
    raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

if not os.path.exists(POST_TEXT_PATH):
    raise Exception(f"[ERROR] 投稿文が存在しません → {POST_TEXT_PATH}")

# -------------------------------
# 投稿文読み込み（generate.py 生成）
# -------------------------------
def load_post_text():
    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

# -------------------------------
# 画像アップロード
# -------------------------------
def upload_file():
    url = f"{MISSKEY_HOST}/api/drive/files/create"
    print(f"[INFO] Uploading image → {url}")

    with open(IMAGE_PATH, "rb") as f:
        r = requests.post(
            url,
            data={"i": MISSKEY_TOKEN},
            files={"file": f}
        )

    if r.status_code != 200:
        raise Exception(f"[ERROR] Upload failed → {r.text}")

    file_id = r.json().get("id")
    if not file_id:
        raise Exception("[ERROR] file_id not found")

    print(f"[OK] Uploaded → file_id={file_id}")
    return file_id

# -------------------------------
# 投稿
# -------------------------------
def main():
    print("[INFO] post_misskey.py started")

    text = load_post_text()

    print("\n--- POST TEXT (Misskey) ---\n" + text + "\n")

    file_id = upload_file()

    payload = {
        "i": MISSKEY_TOKEN,
        "text": text,
        "fileIds": [file_id],
    }

    r = requests.post(
        f"{MISSKEY_HOST}/api/notes/create",
        json=payload
    )

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey 投稿失敗 → {r.text}")

    print("[SUCCESS] Posted to Misskey")

if __name__ == "__main__":
    main()
