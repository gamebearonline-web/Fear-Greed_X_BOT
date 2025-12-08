import os
import requests

MISSKEY_HOST = os.getenv("MISSKEY_HOST")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")  # ← post_text.txt のパス

def load_post_text():
    """X 投稿用に生成した文章を読み込む"""
    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"POST_TEXT_PATH が存在しません: {POST_TEXT_PATH}")
    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def upload_file():
    """Misskey に画像をアップロードして fileId を得る"""
    url = f"{MISSKEY_HOST}/api/drive/files/create"

    with open(IMAGE_PATH, "rb") as f:
        files = {"file": f}
        data = {"i": MISSKEY_TOKEN}
        r = requests.post(url, data=data, files=files)

    if r.status_code != 200:
        raise Exception("Misskey ファイルアップロード失敗: " + r.text)

    file_id = r.json()["id"]
    print(f"[OK] Misskey upload file_id={file_id}")
    return file_id

def main():
    print("[INFO] post_misskey.py started")

    if not MISSKEY_HOST or not MISSKEY_TOKEN:
        raise Exception("MISSKEY_HOST / MISSKEY_TOKEN が設定されていません")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"IMAGE_PATH が存在しません: {IMAGE_PATH}")

    # X の投稿文を artifact から読み込む
    text = load_post_text()
    print("\n--- POST TEXT (Misskey) ---\n" + text + "\n")

    # 画像アップロード
    file_id = upload_file()

    # 投稿本体
    note_url = f"{MISSKEY_HOST}/api/notes/create"
    payload = {
        "i": MISSKEY_TOKEN,
        "text": text,
        "fileIds": [file_id],
    }

    r = requests.post(note_url, json=payload)

    print("Post status:", r.status_code)
    print(r.text)

    if r.status_code != 200:
        raise Exception("Misskey 投稿失敗: " + r.text)

    print("[OK] Posted to Misskey successfully!")

if __name__ == "__main__":
    main()
