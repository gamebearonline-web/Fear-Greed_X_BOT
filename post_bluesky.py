import os
from atproto import Client, models


# ======================================
# 設定
# ======================================
IMAGE_PATH = os.getenv("IMAGE_PATH", "fgi-image/FearGreed_Output.png")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH", "fgi-image/post_text.txt")

BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")


# ======================================
# 投稿本文取得
# ======================================
def load_post_text():
    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


# ======================================
# MAIN
# ======================================
def main():
    print("[INFO] Starting Bluesky posting...")

    if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
        raise RuntimeError("Bluesky credentials are missing")

    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

    text = load_post_text()

    print("----- POST TEXT (Bluesky) -----")
    print(text)

    # ----------------------------------
    # Login
    # ----------------------------------
    client = Client()
    client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    print("[INFO] Bluesky Login OK")

    # ----------------------------------
    # Upload image as blob
    # ----------------------------------
    with open(IMAGE_PATH, "rb") as f:
        blob = client.upload_blob(f)

    print("[INFO] Image uploaded to Bluesky")

    # ----------------------------------
    # Create image embed
    # ----------------------------------
    embed = models.AppBskyEmbedImages.Main(
        images=[
            models.AppBskyEmbedImages.Image(
                image=blob.blob,
                alt="Fear & Greed Index"
            )
        ]
    )

    # ----------------------------------
    # Send post
    # ----------------------------------
    client.send_post(
        text=text,
        embed=embed
    )

    print("[SUCCESS] Bluesky 投稿完了")


# ======================================
# Entry
# ======================================
if __name__ == "__main__":
    main()
