# post_bluesky.py

import os
from atproto import Client

def main():
    print("[INFO] post_bluesky.py started")

    HANDLE = os.getenv("BSKY_HANDLE")
    PASSWORD = os.getenv("BSKY_APP_PASSWORD")
    IMAGE_PATH = os.getenv("IMAGE_PATH")

    if not HANDLE or not PASSWORD:
        raise Exception("Bluesky 認証情報が不足しています（BSKY_HANDLE / BSKY_APP_PASSWORD）")

    if not IMAGE_PATH:
        raise Exception("IMAGE_PATH が設定されていません")

    client = Client()
    client.login(HANDLE, PASSWORD)

    with open(IMAGE_PATH, "rb") as f:
        img = f.read()

    client.send_post(
        text="Fear & Greed Index（Bluesky 自動投稿）",
        embed=client.upload_blob(img)
    )

    print("[OK] Posted to Bluesky")

if __name__ == "__main__":
    main()
