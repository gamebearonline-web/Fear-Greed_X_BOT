import os
from atproto import Client
from atproto.exceptions import AtProtocolError

BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")

def load_post_text():
    print(f"[DEBUG] Loading post text from: {POST_TEXT_PATH}")

    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"[ERROR] post_text.txt が見つかりません → {POST_TEXT_PATH}")

    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def main():
    print("[INFO] post_bluesky.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

    # 投稿文
    text = load_post_text()
    print("\n--- POST TEXT (Bluesky) ---\n" + text + "\n")

    # Bluesky Login
    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky Login Failed → {e}")

    # Upload Image
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    blob = client.upload_blob(img_bytes)
    embed = client.get_embed_image(blob, "Fear & Greed Index")

    # Post
    client.create_post(text=text, embed=embed)
    print("[OK] Posted to Bluesky successfully!")


if __name__ == "__main__":
    main()
