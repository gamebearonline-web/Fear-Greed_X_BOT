# ==========================================
# post_x.py（tweepy V1 画像 + V2 投稿 / 完全版）
# ==========================================
import os
import sys
import tweepy
import requests
from datetime import datetime, timedelta
import pytz

# ======================================================
#  OAUTH1 / OAUTH2 認証情報
# ======================================================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print("[ERROR] Twitter API credentials が不足しています")
    sys.exit(1)

# ======================================================
#  Fear & Greed Index API
# ======================================================
def value_to_label(v):
    if v <= 24:  return "Extreme Fear"
    if v <= 44:  return "Fear"
    if v <= 55:  return "Neutral"
    if v <= 75:  return "Greed"
    return "Extreme Greed"


def diff(now, prev):
    d = now - prev
    if d > 0:
        return f"(+{d})"
    if d < 0:
        return f"({d})"
    return "(±0)"


def get_stock_fgi():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }
    data = requests.get(url, headers=headers).json()
    fgi = data["fgi"]

    now = int(fgi["now"]["value"])
    prev = int(fgi["previousClose"]["value"])
    return now, prev, value_to_label(now)


def get_crypto_fgi():
    url = "https://api.alternative.me/fng/?limit=2"
    d = requests.get(url).json()["data"]

    now = int(d[0]["value"])
    prev = int(d[1]["value"])
    return now, prev, value_to_label(now)

# ======================================================
# 投稿文作成
# ======================================================
def build_post_text():
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst)
    today = now.strftime("%Y/%m/%d（%a）")

    stock_now, stock_prev, stock_label = get_stock_fgi()
    crypto_now, crypto_prev, crypto_label = get_crypto_fgi()

    return (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{today}\n\n"
        f"⬜Stock：{stock_now}{diff(stock_now, stock_prev)}【{stock_label}】\n"
        f"🟧Bitcoin：{crypto_now}{diff(crypto_now, crypto_prev)}【{crypto_label}】"
    )

# ======================================================
#   X 投稿処理
# ======================================================
def upload_media_v1(image_path):
    """画像を V1 API でアップロード"""
    try:
        auth = tweepy.OAuth1UserHandler(
            API_KEY, API_SECRET,
            ACCESS_TOKEN, ACCESS_SECRET
        )
        api = tweepy.API(auth)
        media = api.media_upload(filename=image_path)
        media_id = str(media.media_id)
        print(f"[INFO] Media uploaded → media_id={media_id}")
        return media_id
    except Exception as e:
        print("[ERROR] 画像アップロード失敗:", repr(e))
        sys.exit(1)


def post_tweet_v2(text, media_id):
    """V2 API でツイート投稿"""
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET
        )

        response = client.create_tweet(
            text=text,
            media_ids=[media_id]
        )

        tweet_id = response.data["id"]

        # ユーザー名取得（安全に）
        try:
            user_info = client.get_me()
            username = user_info.data.username if user_info.data else "unknown"
        except:
            username = "unknown"

        print(f"[SUCCESS] 投稿完了 → https://x.com/{username}/status/{tweet_id}")
        print("\n--- 投稿内容 ---\n" + text)

    except Exception as e:
        print("[ERROR] ツイート投稿失敗:", repr(e))
        sys.exit(1)

# ======================================================
# MAIN
# ======================================================
def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        print(f"[ERROR] 画像が見つかりません → {IMAGE_PATH}")
        sys.exit(1)

    # 投稿文生成
    text = build_post_text()

    # 画像アップロード
    media_id = upload_media_v1(IMAGE_PATH)

    # 投稿
    post_tweet_v2(text, media_id)

    print("[DONE] X 投稿完了")


if __name__ == "__main__":
    main()
