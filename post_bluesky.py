# ==========================================
# post_bluesky.py（FGI / Bluesky投稿・完全安定版）
# ==========================================
import os
import requests
from datetime import datetime, timedelta
from atproto import Client
from atproto.exceptions import AtProtocolError

# -------------------------------
# 🔐 環境変数チェック（スプラ方式）
# -------------------------------
BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
    raise Exception("[ERROR] Bluesky の環境変数（BSKY_HANDLE / BSKY_APP_PASSWORD）が不足しています")

if not RAPIDAPI_KEY:
    raise Exception("[ERROR] RAPIDAPI_KEY が未設定です（必須）")

# --------------------------------------------------------
#  日付処理（日本時間）
# --------------------------------------------------------
def get_today_text():
    now = datetime.utcnow() + timedelta(hours=9)
    weekday = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return f"{now.strftime('%Y/%m/%d')}（{weekday}）"

# --------------------------------------------------------
#  FGI 共通ラベル
# --------------------------------------------------------
def value_to_label(v):
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 55: return "Neutral"
    if v <= 75: return "Greed"
    return "Extreme Greed"

# --------------------------------------------------------
#  Stock FGI（RapidAPI）
# --------------------------------------------------------
def get_stock_fgi_with_prev():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    res = requests.get(url, headers=headers)
    try:
        data = res.json()
    except Exception as e:
        print("[ERROR] RapidAPI JSON Decode Error:", e)
        print("[ERROR] Response:", res.text)
        raise

    print("[DEBUG] RapidAPI Response:", data)

    if "fgi" in data:
        fgi = data["fgi"]
    elif "data" in data:
        fgi = data["data"]
    else:
        raise Exception(f"[ERROR] FGI データが見つかりません → {data}")

    try:
        now = int(fgi["now"]["value"])
        prev = int(fgi["previousClose"]["value"])
    except Exception as e:
        print("[ERROR] FGI 構造違い:", fgi)
        raise e

    return now, prev, value_to_label(now)

# --------------------------------------------------------
#  Crypto FGI（alternative.me）
# --------------------------------------------------------
def get_crypto_fgi_with_prev():
    url = "https://api.alternative.me/fng/?limit=2"
    data = requests.get(url).json()

    try:
        now = int(data["data"][0]["value"])
        prev = int(data["data"][1]["value"])
    except Exception as e:
        print("[ERROR] Crypto FGI API構造:", data)
        raise e

    return now, prev, value_to_label(now)

# --------------------------------------------------------
#  差分表記
# --------------------------------------------------------
def diff(now, prev):
    d = now - prev
    if d > 0: return f"(+{d})"
    if d < 0: return f"({d})"
    return "(±0)"

# --------------------------------------------------------
#  投稿文作成
# --------------------------------------------------------
def build_post_text():
    today = get_today_text()

    stock_now, stock_prev, stock_label = get_stock_fgi_with_prev()
    crypto_now, crypto_prev, crypto_label = get_crypto_fgi_with_prev()

    return (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{today}\n\n"
        f"⬜Stock：{stock_now}{diff(stock_now, stock_prev)}【{stock_label}】\n"
        f"🟧Bitcoin：{crypto_now}{diff(crypto_now, crypto_prev)}【{crypto_label}】"
    )

# --------------------------------------------------------
#  Bluesky 投稿処理
# --------------------------------------------------------
def main():
    print("[INFO] Starting Bluesky posting...")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

    # 投稿文生成
    text = build_post_text()
    print("\n----- POST TEXT (Bluesky) -----\n" + text + "\n")

    # ログイン
    client = Client()
    try:
        client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
        print("[INFO] Bluesky Login OK")
    except AtProtocolError as e:
        raise Exception(f"[ERROR] Bluesky Login Failed → {e}")

    # 画像ロード
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    # 画像アップロード（contentType を明示）
    try:
        blob = client.upload_blob(img_bytes, encoding="image/png")
    except Exception as e:
        raise Exception(f"[ERROR] 画像アップロード失敗 → {e}")

    # 投稿準備
    embed = client.get_embed_image(blob, "Fear & Greed Index")

    # 投稿実行
    try:
        client.create_post(text=text, embed=embed)
    except Exception as e:
        raise Exception(f"[ERROR] Bluesky 投稿失敗 → {e}")

    print("[SUCCESS] 投稿完了（Bluesky）")


if __name__ == "__main__":
    main()
