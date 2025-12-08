# ==========================================
# post_bluesky.py（独立生成・完全版）
# ==========================================
import os
import requests
from datetime import datetime, timedelta
from atproto import Client
from atproto.exceptions import AtProtocolError

# -------------------------------
# 🔐 環境変数
# -------------------------------
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


# ==========================================
# 共通ロジック（X版と同じ）
# ==========================================

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


# --- Stock FGI ---
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


# --- Crypto FGI ---
def get_crypto_fgi_with_prev():
    data = requests.get("https://api.alternative.me/fng/?limit=2").json()["data"]

    now = int(data[0]["value"])
    prev = int(data[1]["value"])
    label = value_to_label(now)
    return now, prev, label


def diff(now, prev):
    d = now - prev
    if d > 0:  return f"(+{d})"
    if d < 0:  return f"({d})"
    return "(±0)"


# --- Bluesky 投稿文生成 ---
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


# ==========================================
# Bluesky 投稿処理
# ==========================================
def main():
    print("[INFO] post_bluesky.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

    # 投稿文生成（post_text.txt は使わない）
    text = build_post_text()
    print("\n--- POST TEXT (Bluesky) ---\n" + text + "\n")

    # Bluesky Login
    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky ログイン失敗 → {e}")

    # 画像アップロード
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    blob = client.upload_blob(img_bytes)
    embed = client.get_embed_image(blob, "Fear & Greed Index")

    # 投稿
    try:
        client.create_post(text=text, embed=embed)
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky 投稿失敗 → {e}")

    print("[OK] Posted to Bluesky successfully!")


if __name__ == "__main__":
    main()
