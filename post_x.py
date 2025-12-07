import os
import requests
from requests_oauthlib import OAuth1
from datetime import datetime

# =====================
#  OAuth1 認証
# =====================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

IMAGE_PATH = os.getenv("IMAGE_PATH")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


# =====================
#  日付（曜日付き）を生成
# =====================
def get_today_text():
    # 日本時間
    now = datetime.utcnow()
    jst = now.replace(hour=now.hour + 9)

    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
    w = weekday_map[jst.weekday()]

    return f"{jst.strftime('%Y/%m/%d')}（{w}）"


# =====================
#  投稿文を生成
# =====================
def build_post_text():
    today_text = get_today_text()
    return f"CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n{today_text}"


# =====================
#  画像アップロード
# =====================
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


# =====================
#  ツイート投稿
# =====================
def post_tweet(text, media_id):
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text, "media": {"media_ids": [media_id]}}

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=auth, json=payload, headers=headers)

    print("Tweet status:", response.status_code)
    print(response.text)

    if response.status_code not in [200, 201]:
        raise Exception(f"Tweet Failed: {response.text}")


# =====================
#  メイン処理
# =====================
def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH:
        raise Exception("IMAGE_PATH が設定されていません")

    # 投稿文を自動生成
    post_text = build_post_text()
    print(f"[INFO] POST_TEXT = {post_text}")

    # 画像 upload
    media_id = upload_media(IMAGE_PATH)

    # 投稿
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")


if __name__ == "__main__":
    main()
