import os
import requests
from requests_oauthlib import OAuth1
from post_common import build_post_text

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
IMAGE_PATH = os.getenv("IMAGE_PATH")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


def upload_media(image_path):
    url = "https://upload.twitter.com/1.1/media/upload.json"

    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, auth=auth, files=files)

    if response.status_code != 200:
        raise Exception(f"Media Upload Failed: {response.text}")

    media_id = response.json()["media_id_string"]
    print(f"[OK] Media uploaded → {media_id}")
    return media_id


def post_tweet(text, media_id):
    url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {"status": text, "media_ids": media_id}

    response = requests.post(url, auth=auth, data=payload)

    print("Tweet status:", response.status_code)
    print(response.text)

    if response.status_code != 200:
        raise Exception(f"Tweet Failed: {response.text}")


def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH:
        raise Exception("IMAGE_PATH が設定されていません")

    # ❗ GAS は投稿文を作らない → Python で生成
    post_text = build_post_text()

    print("\n=== POST TEXT ===\n" + post_text + "\n")

    media_id = upload_media(IMAGE_PATH)
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")

    # Bluesky / Misskey 用に保存
    with open("post_text.txt", "w", encoding="utf-8") as f:
        f.write(post_text)

    print("[OK] Saved post_text.txt for Bluesky / Misskey")


if __name__ == "__main__":
    main()
