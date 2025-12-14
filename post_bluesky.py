# ==========================================
# post_bluesky.py（スプラ方式・最終版）
# ==========================================
import os
from atproto import Client
from atproto.exceptions import AtProtocolError

# -------------------------------
# 🔐 環境変数
# -------------------------------
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")

if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
    raise Exception("[ERROR] Bluesky の認証情報が不足しています")

if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
    raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

# -------------------------------
# 投稿文（確定済み文字列）
# -------------------------------
def build_post_text():
    return "CNN・Crypto Fear & Greed Index\n#FearAndGreed #Bitcoin"

# -------------------------------
# Bluesky 投稿
# -------------------------------
def main():
    print("[INFO] Starting Bluesky posting...")

    text = build_post_text()
    print("\n----- POST TEXT (Bluesky) -----\n" + text + "\n")

    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
        print("[INFO] Bluesky Login OK")
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky Login Failed → {e}")

    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    blob = client.upload_blob(img_bytes, encoding="image/png")
    embed = client.get_embed_image(blob, "Fear & Greed Index")

    client.create_post(text=text, embed=embed)

    print("[SUCCESS] 投稿完了（Bluesky）")


if __name__ == "__main__":
    main()
