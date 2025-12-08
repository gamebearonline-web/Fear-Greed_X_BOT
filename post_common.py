# post_common.py
import os
import requests
from datetime import datetime, timedelta

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# ----------------------------------------
# JST 今日の日付
# ----------------------------------------
def get_today_text():
    now = datetime.utcnow() + timedelta(hours=9)
    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]
    return f"{now.strftime('%Y/%m/%d')}（{weekday_map[now.weekday()]}）"


# ----------------------------------------
# ラベル判定
# ----------------------------------------
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


# ----------------------------------------
# Stock FGI
# ----------------------------------------
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


# ----------------------------------------
# Crypto FGI
# ----------------------------------------
def get_crypto_fgi_with_prev():
    data = requests.get("https://api.alternative.me/fng/?limit=2").json()["data"]

    now = int(data[0]["value"])
    prev = int(data[1]["value"])
    label = value_to_label(now)

    return now, prev, label


# ----------------------------------------
# 差分
# ----------------------------------------
def diff(now, prev):
    d = now - prev
    if d > 0:
        return f"(+{d})"
    elif d < 0:
        return f"({d})"
    else:
        return "(±0)"


# ----------------------------------------
# 投稿文生成（X / Bsky / Misskey 共通）
# ----------------------------------------
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
