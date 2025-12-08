# post_misskey.py

import os
import requests

def main():
    print("[INFO] post_misskey.py started")

    HOST = os.getenv("MISSKEY_HOST")
    TOKEN = os.getenv("MISSKEY_TOKEN")
    IMAGE_PATH = os.getenv("IMAGE_PATH")

    if not HOST or not TOKEN:
        raise Exception("Misskey 認証情報不足（MISSKEY_HOST / MISSKEY_TOKEN）")

    if not IMAGE_PATH:
        raise Exception("IMAGE_PATH が設定されていません")

    # Step 1: 画像アップロード
    url_upload = f"{HOST}/api/drive/files/create"
    files = {"file": open(IMAGE_PATH, "rb")}
    payload = {"i": TOKEN}

    res = requests.post(url_upload, data=payload, files=files).json()
    file_id = res["id"]

    # Step 2: 投稿
    url_note = f"{HOST}/api/notes/create"
    payload = {
        "i": TOKEN,
        "text": "Fear & Greed Index（Misskey 自動投稿）",
        "fileIds": [file_id],
    }

    res2 = requests.post(url_note, json=payload)
    print("[OK] Misskey response:", res2.text)

if __name__ == "__main__":
    main()
