# ==========================================
# post_x.py（独立生成・独立投稿・完全安定版）
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


# ======================================================
#  共通関数
# ======================================================

def get_today_text():
    now = datetime.utcnow() + timedelta(hours=9)
    weekday = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return f"{now.strftime('%Y/%m/%d')}（{weekday}）"


def value_to_label(v):
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 55: return "Neutral"
    if v <= 75: return "Greed"
    return "Extreme Greed"


# ======================================================
#  🔥 安定版 Stock FGI 取得
# ======================================================
def get_stock_fgi_with_prev():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    res = requests.get(url, headers=headers)
    data = res.json()

    print("[DEBUG] Stock FGI Response:", data)

    # --- fgi がない場合（APIエラーなど）
    if "fgi" not in data:
        raise Exception(f"[ERROR] API returned unexpected format → {data}")

    fgi = data["fgi"]

    now = int(fgi["now"]["value"])
    prev = int(fgi["previousClose"]["value"])
    label = value_to_label(now)

    return now, prev, label


# ======================================================
#  Crypto FGI
# ======================================================
def get_crypto_fgi_with_prev():
    url = "https://api.alternative.me/fng/?limit=2"
    res = requests.get(url)
    data = res.json()

    print("[DEBUG] Crypto FGI Response:", data)

    if "data" not in data:
        raise Exception(f"[ERROR] Crypto API format error → {data}")

    now = int(data["data"][0]["value"])
    prev = int(data["data"][1]["value"])
    label = value_to_label(now)

    return now, prev, label


def diff(now, prev):
    d = now - prev
    if d > 0:  return f"(+{d})"
    if d < 0:  return f"({d})"
    return "(±0)"


# ======================================================
#  投稿文生成
# ======================================================
def build_post_text():
    today = get_today_text()

    stock_now, stock_prev, stock_label = get_stock_fgi_with_prev()
    crypto_now, crypto_prev, crypto_label = get_crypto_fgi_with_prev()

    stock_diff = diff(stock_now, stock_prev)
    crypto_diff = diff(crypto_now, crypto_prev)

    return (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{today}\n\n"
        f"⬜Stock：{stock_now}{stock_diff}【{stock_label}】\n"
        f"🟧Bitcoin：{crypto_now}{crypto_diff}【{crypto_label}】"
    )


# ======================================================
#  X投稿
# ======================================================
def upload_media(path):
    url = "https://upload.twitter.com/1.1/media/upload.json"
    with open(path, "rb") as f:
        res = requests.post(url, auth=auth, files={"media": f})

    if res.status_code != 200:
        raise Exception(f"[ERROR] Media Upload Failed: {res.text}")

    media_id = res.json()["media_id_string"]
    print("[OK] Uploaded media:", media_id)
    return media_id


def post_tweet(text, media_id):
    url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {"status": text, "media_ids": media_id}

    res = requests.post(url, auth=auth, data=payload)
    print("Tweet Response:", res.status_code, res.text)

    if res.status_code != 200:
        raise Exception(f"[ERROR] Tweet Failed: {res.text}")


# ======================================================
#  MAIN
# ======================================================
def main():
    print("[INFO] post_x.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] IMAGE_PATH が存在しません → {IMAGE_PATH}")

    # 投稿文生成（ここが落ちないように改良済み）
    text = build_post_text()

    media_id = upload_media(IMAGE_PATH)
    post_tweet(text, media_id)

    print("[SUCCESS] X投稿完了！")


if __name__ == "__main__":
    main()
