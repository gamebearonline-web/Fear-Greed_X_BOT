import os
import requests

MISSKEY_HOST = os.getenv("MISSKEY_HOST")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")

def load_post_text():
    print(f"[DEBUG] Loading post text from: {POST_TEXT_PATH}")

    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"[ERROR] post_text.txt が見つかりません → {POST_TEXT_PATH}")

    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def upload_file():
    url = f"{MISSKEY_HOST}/api/drive/files/create"
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": f}
        data = {"i": MISSKEY_TOKEN}
        r = requests.post(url, data=data, files=files)

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey ファイルアップロード失敗: {r.text}")

    file_id = r.json().get("id")
    if not file_id:
        raise Exception("[ERROR] file_id がありません")

    print(f"[OK] Misskey uploaded → {file_id}")
    return file_id


def main():
    print("[INFO] post_misskey.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] 画像がありません → {IMAGE_PATH}")

    text = load_post_text()
    print("\n--- POST TEXT (Misskey) ---\n" + text + "\n")

    file_id = upload_file()

    payload = {
        "i": MISSKEY_TOKEN,
        "text": text,
        "fileIds": [file_id],
    }

    note_url = f"{MISSKEY_HOST}/api/notes/create"
    r = requests.post(note_url, json=payload)

    print("Post status:", r.status_code)

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey 投稿失敗: {r.text}")

    print("[OK] Posted to Misskey successfully!")


if __name__ == "__main__":
    main()
