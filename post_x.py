# post_x.py
import os
import requests
from requests_oauthlib import OAuth1

# =============================
# 🔐 環境変数（GitHub Secrets）
# =============================
API_KEY        = os.getenv("TWITTER_API_KEY")
API_SECRET     = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN   = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET  = os.getenv("TWITTER_ACCESS_SECRET")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


# =============================
# 📤 メディアアップロード（v1.1）
# =============================
def upload_media(image_path):
    print(f"[UPLOAD] Uploading media → {image_path}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    url = "https://upload.twitter.com/1.1/media/upload.json"

    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, auth=auth, files=files)

    if response.status_code != 200:
        raise Exception(f"[ERROR] Media Upload Failed: {response.text}")

    media_id = response.json()["media_id_string"]
    print(f"[OK] Media uploaded → {media_id}")

    return media_id


# =============================
# 📝 ツイート投稿（v2）
# =============================
def post_tweet(text, media_id):
    print(f"[POST] Posting tweet...")

    url = "https://api.twitter.com/2/tweets"
    payload = {
        "text": text,
        "media": {"media_ids": [media_id]},
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        url,
        auth=auth,
        json=payload,
        headers=headers
    )

    print("Tweet status:", response.status_code)
    print(response.text)

    if response.status_code not in [200, 201]:
        raise Exception(f"[ERROR] Tweet Failed: {response.text}")

    print("[OK] Tweet posted successfully!")


# =============================
# 🚀 外部呼び出し用（main.py から使う関数）
# =============================
def post_to_x(image_path, text):
    """
    main.py から呼び出せる統一関数
    """
    print("=== post_to_x START ===")
    media_id = upload_media(image_path)
    post_tweet(text, media_id)
    print("=== post_to_x END ===")


# =============================
# 🏃 スクリプト単体実行用
# =============================
def main():
    IMAGE_PATH = os.getenv("IMAGE_PATH")
    POST_TEXT  = os.getenv("POST_TEXT")

    print("[INFO] post_x.py started")

    if not IMAGE_PATH:
        raise Exception("❌ ERROR: IMAGE_PATH が設定されていません")

    if not POST_TEXT:
        raise Exception("❌ ERROR: POST_TEXT が空です。workflow_dispatch で渡してください。")

    post_to_x(IMAGE_PATH, POST_TEXT)


if __name__ == "__main__":
    main()
