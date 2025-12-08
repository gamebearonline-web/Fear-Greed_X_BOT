import os
import requests
from requests_oauthlib import OAuth1

# ==========================
#  OAuth1 認証
# ==========================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
IMAGE_PATH = os.getenv("IMAGE_PATH", "output/FearGreed_Output.png")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


# ==========================
# 投稿文を読み込む（GAS が生成したもの）
# ==========================
def load_post_text():
    path = "post_text.txt"
    if not os.path.exists(path):
        raise Exception("post_text.txt が存在しません（GAS が生成していません）")

    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ==========================
# メディアアップロード
# ==========================
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


# ==========================
# v1.1 ツイート投稿（OAuth1 専用）
# ==========================
def post_tweet(text, media_id):
    url = "https://api.twitter.com/1.1/statuses/update.json"

    payload = {
        "status": text,
        "media_ids": media_id
    }

    response = requests.post(url, auth=auth, data=payload)

    print("Tweet status:", response.status_code)
    print(response.text)

    if response.status_code != 200:
        raise Exception(f"Tweet Failed: {response.text}")


# ==========================
# メイン処理
# ==========================
def main():
    print("[INFO] post_x.py started")

    # 投稿文（GAS生成）を読み込む
    post_text = load_post_text()
    print("\n=== POST TEXT ===\n" + post_text + "\n")

    # 投稿画像パス確認
    if not os.path.exists(IMAGE_PATH):
        raise Exception(f"画像が存在しません: {IMAGE_PATH}")

    # X 投稿
    media_id = upload_media(IMAGE_PATH)
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")


if __name__ == "__main__":
    main()
