import os
from atproto import Client
from atproto.exceptions import AtProtocolError

# ==============================
# 環境変数
# ==============================
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")   # ← post_text.txt のパス


def load_post_text():
    """X workflow が生成した投稿文を読み込む"""
    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"[ERROR] POST_TEXT_PATH が存在しません → {POST_TEXT_PATH}")

    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def main():
    print("[INFO] post_bluesky.py started")

    # --- 環境変数チェック ---
    if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
        raise Exception("[ERROR] BSKY_HANDLE / BSKY_APP_PASSWORD が設定されていません")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] IMAGE_PATH が存在しません → {IMAGE_PATH}")

    # --- 投稿文 ---
    text = load_post_text()
    print("\n--- POST TEXT (Bluesky) ---\n" + text + "\n")

    # --- Bluesky ログイン ---
    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky Login Failed → {e}")

    # --- 画像読み込み ---
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    # --- Bluesky に画像アップロード ---
    try:
        blob = client.upload_blob(img_bytes)
    except Exception as e:
        raise Exception(f"[ERROR] Image Upload Failed → {e}")

    # --- embed（画像埋め込み）作成 ---
    embed = client.get_embed_image(blob, alt="Fear & Greed Index")

    # --- 投稿（正式メソッド） ---
    try:
        client.send_post(text=text, embed=embed)
        print("[OK] Posted to Bluesky successfully!")
    except Exception as e:
        raise Exception(f"[ERROR] Bluesky Post Failed → {e}")


if __name__ == "__main__":
    main()
