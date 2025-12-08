# ==========================================
# post_misskey.py（独立生成・完全版）
# ==========================================
import os
import requests
from datetime import datetime, timedelta

MISSKEY_HOST = os.getenv("MISSKEY_HOST")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# ==========================================
# 共通ロジック（X / Bluesky と同じ）
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


# --- Misskey 投稿文生成 ---
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
# Misskey 投稿
# ==========================================

def upload_file():
    url = f"{MISSKEY_HOST}/api/drive/files/create"
    print(f"[INFO] Uploading image to Misskey → {url}")

    with open(IMAGE_PATH, "rb") as f:
        files = {"file": f}
        data = {"i": MISSKEY_TOKEN}
        r = requests.post(url, data=data, files=files)

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey ファイルアップロード失敗: {r.text}")

    file_id = r.json().get("id")
    if not file_id:
        raise Exception("[ERROR] file_id がありません")

    print(f"[OK] Misskey uploaded → {file_id}")
    return file_id


def main():
    print("[INFO] post_misskey.py started")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] 画像がありません → {IMAGE_PATH}")

    # 投稿文生成（post_text.txt は使わない）
    text = build_post_text()
    print("\n--- POST TEXT (Misskey) ---\n" + text + "\n")

    # 画像アップロード
    file_id = upload_file()

    # 投稿
    payload = {
        "i": MISSKEY_TOKEN,
        "text": text,
        "fileIds": [file_id],
    }

    note_url = f"{MISSKEY_HOST}/api/notes/create"
    r = requests.post(note_url, json=payload)

    print("Post status:", r.status_code)

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey 投稿失敗: {r.text}")

    print("[OK] Posted to Misskey successfully!")


if __name__ == "__main__":
    main()
