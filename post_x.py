import os
import requests
from requests_oauthlib import OAuth1
from datetime import datetime, timedelta

# ==========================
#  OAuth1 認証
# ==========================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)


# ==========================
# JST 今日の日付
# ==========================
def get_today_text():
    now = datetime.utcnow() + timedelta(hours=9)
    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
    return f"{now.strftime('%Y/%m/%d')}（{weekday_map[now.weekday()]}）"


# ==========================
# ラベル判定
# ==========================
def value_to_label(v):
    if v <= 24:
        return "Extreme Fear"
    elif v <= 44:
        return "Fear"
    elif v <= 55:
        return "Neutral"
    elif v <= 75:
        return "Greed"
    else:
        return "Extreme Greed"


# ==========================
# Stock FGI（前回との差含む）
# ==========================
def get_stock_fgi_with_prev():
    if not RAPIDAPI_KEY:
        raise Exception("RAPIDAPI_KEY が設定されていません（Stock FGI 用）")

    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    data = requests.get(url, headers=headers).json()["fgi"]

    now = int(data["now"]["value"])
    prev = int(data["previousClose"]["value"])
    label = value_to_label(now)

    return now, prev, label


# ==========================
# Crypto FGI（前回との差含む）
# ==========================
def get_crypto_fgi_with_prev():
    data = requests.get("https://api.alternative.me/fng/?limit=2").json()["data"]

    now = int(data[0]["value"])
    prev = int(data[1]["value"])
    label = value_to_label(now)

    return now, prev, label


# ==========================
# 差分
# ==========================
def diff(now, prev):
    d = now - prev
    if d > 0:
        return f"(+{d})"
    elif d < 0:
        return f"({d})"
    else:
        return "(±0)"


# ==========================
# 投稿文生成
# ==========================
from post_common import build_post_text



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

    post_text = build_post_text()
    print("\n=== POST TEXT ===\n" + post_text + "\n")

    media_id = upload_media(IMAGE_PATH)
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")


if __name__ == "__main__":
    main()
