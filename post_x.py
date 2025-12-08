import os
import requests
from requests_oauthlib import OAuth1
from post_common import build_post_text   # ← 共通テキスト生成を使用

# ==========================
#  OAuth1 認証
# ==========================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
IMAGE_PATH = os.getenv("IMAGE_PATH")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


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
# ツイート投稿
# ==========================
def post_tweet(text, media_id):
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text, "media": {"media_ids": [media_id]}}

    response = requests.post(
        url,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"},
    )

    print("Tweet status:", response.status_code)
    print(response.text)

    if response.status_code not in [200, 201]:
        raise Exception(f"Tweet Failed: {response.text}")


# ==========================
# メイン処理
# ==========================
def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH:
        raise Exception("IMAGE_PATH が設定されていません（投稿画像パス）")

    # 共通投稿文を作成
    post_text = build_post_text()
    print("\n=== POST TEXT ===\n" + post_text + "\n")

    # X 投稿
    media_id = upload_media(IMAGE_PATH)
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")

    # ★ 他SNS用に投稿文を保存
    with open("post_text.txt", "w", encoding="utf-8") as f:
        f.write(post_text)

    print("[OK] Saved post_text.txt for Bluesky / Misskey")


if __name__ == "__main__":
    main()
