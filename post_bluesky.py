import os
from atproto import Client
from datetime import datetime

# ==============================
# 環境変数
# ==============================
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")   # ← post_text.txt のパス

def load_post_text():
    """X の workflow が作成した投稿文を読み込む"""
    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"POST_TEXT_PATH が存在しません: {POST_TEXT_PATH}")
    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def main():
    print("[INFO] post_bluesky.py started")

    if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
        raise Exception("BSKY_HANDLE / BSKY_APP_PASSWORD が設定されていません")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"IMAGE_PATH が存在しません: {IMAGE_PATH}")

    # 投稿文を読み込む
    text = load_post_text()
    print("\n--- POST TEXT (Bluesky) ---\n" + text + "\n")

    # Bluesky ログイン
    client = Client()
    client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)

    # 画像読み込み
    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()

    # 画像アップロード
    uploaded = client.upload_blob(image_bytes)

    # 投稿
    client.send_post(text=text, embed=client.get_embed_image(uploaded, "Fear & Greed Index"))
    print("[OK] Posted to Bluesky successfully!")

if __name__ == "__main__":
    main()
