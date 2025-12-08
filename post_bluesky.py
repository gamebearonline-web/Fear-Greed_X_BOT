# post_bluesky.py
import os
from atproto import Client
from post_common import build_post_text

def main():
    print("[INFO] post_bluesky.py started")

    HANDLE = os.getenv("BSKY_HANDLE")
    PASSWORD = os.getenv("BSKY_APP_PASSWORD")
    IMAGE_PATH = os.getenv("IMAGE_PATH")

    text = build_post_text()

    client = Client()
    client.login(HANDLE, PASSWORD)

    with open(IMAGE_PATH, "rb") as f:
        img = f.read()

    client.send_post(
        text=text,
        embed=client.upload_blob(img)
    )

    print("[OK] Posted to Bluesky")

if __name__ == "__main__":
    main()
