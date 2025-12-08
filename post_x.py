# ==========================================
# post_x.py（post_common 統合版 / 完全版）
# ==========================================
import os
import requests
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1

# -------------------------------
# 🔐 環境変数
# -------------------------------
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

# ==========================================
#  共通関数（post_common.py の統合部分）
# ==========================================

# -------------------------------
# JST 今日
# -------------------------------
def get_today_text():
    now = datetime.utcnow() + timedelta(hours=9)
    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
    return f"{now.strftime('%Y/%m/%d')}（{weekday_map[now.weekday()]}）"


# -------------------------------
# ラベル判定
# -------------------------------
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


# -------------------------------
# Stock FGI（RapidAPI）
# -------------------------------
def get_stock_fgi_with_prev():
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


# -------------------------------
# Crypto FGI（alternative.me）
# -------------------------------
def get_crypto_fgi_with_prev():
    data = requests.get("https://api.alternative.me/fng/?limit=2").json()["data"]

    now = int(data[0]["value"])
    prev = int(data[1]["value"])
    label = value_to_label(now)

    return now, prev, label


# -------------------------------
# 差分
# -------------------------------
def diff(now, prev):
    d = now - prev
    if d > 0:
        return f"(+{d})"
    elif d < 0:
        return f"({d})"
    else:
        return "(±0)"


# -------------------------------
# 投稿文作成（X / Bluesky / Misskey 共通）
# -------------------------------
def build_post_text():
    today = get_today_text()

    stock_now, stock_prev, stock_label = get_stock_fgi_with_prev()
    crypto_now, crypto_prev, crypto_label = get_crypto_fgi_with_prev()

    stock_diff = diff(stock_now, stock_prev)
    crypto_diff = diff(crypto_now, crypto_prev)

    text = (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{today}\n\n"
        f"⬜Stock：{stock_now}{stock_diff}【{stock_label}】\n"
        f"🟧Bitcoin：{crypto_now}{crypto_diff}【{crypto_label}】"
    )

    return text


# ==========================================
#  X（Twitter）投稿処理
# ==========================================

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


# ==========================================
#  メイン処理
# ==========================================
def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"IMAGE_PATH が存在しません → {IMAGE_PATH}")

    # 投稿文生成（post_common 統合済み）
    post_text = build_post_text()

    print("\n=== POST TEXT ===\n" + post_text + "\n")

    # X 投稿
    media_id = upload_media(IMAGE_PATH)
    post_tweet(post_text, media_id)

    print("[OK] Tweet posted successfully!")

    # Bluesky / Misskey 用に保存
    with open("post_text.txt", "w", encoding="utf-8") as f:
        f.write(post_text)

    print("[OK] Saved post_text.txt for Bluesky / Misskey")


if __name__ == "__main__":
    main()
