# generate.py

from PIL import Image, ImageDraw, ImageFont
import requests
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import math

# ------------------------------------------------------------
#  Google Sheets 認証（GitHub Actions 対応）
# ------------------------------------------------------------
def get_sheet(sheet_name):
    print(f"[INFO] Connecting to Google Sheet → {sheet_name}")

    SHEET_ID = "1YS3tyCuduXf9SDhbgEOv74f5RHSapa8kBw5y979EYO0"

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service-account.json", scope
    )
    client = gspread.authorize(creds)

    return client.open_by_key(SHEET_ID).worksheet(sheet_name)


# ------------------------------------------------------------
#  Crypto：1年前データ取得
# ------------------------------------------------------------
def get_crypto_one_year_ago():
    ws = get_sheet("CryptoGreedFear")

    d = datetime.now() - timedelta(days=365)
    target = f"{d.year}/{d.month}/{d.day}"
    print(f"[INFO] Searching 1-year-ago Crypto value → {target}")

    rows = ws.get_all_values()
    for r in rows[1:]:
        if r[0] == target:
            print(f"[FOUND] Crypto 1y ago = {r[1]}")
            return int(r[1])

    print("[WARN] 1-year-ago Crypto not found")
    return None


# ------------------------------------------------------------
#  RapidAPI：株式 Fear & Greed
# ------------------------------------------------------------
def get_stock_fgi():
    print("[INFO] Requesting Stock FGI from RapidAPI")

    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    d = requests.get(url, headers=headers).json()["fgi"]

    print("[DATA] Stock FGI received →", d)

    return {
        "now": d["now"]["value"],
        "1_day_ago": d["previousClose"]["value"],
        "1_week_ago": d["oneWeekAgo"]["value"],
        "1_month_ago": d["oneMonthAgo"]["value"],
        "1_year_ago": d["oneYearAgo"]["value"],
    }


# ------------------------------------------------------------
#  Stock FGI（履歴追加）
# ------------------------------------------------------------
def append_stock_history(stock):
    ws = get_sheet("StockFear&Greed")
    print("[INFO] Adding Stock history data to Sheet...")

    existing = {r[0] for r in ws.get_all_values()[1:]}
    today = datetime.now()

    data_points = [
        (today,                     stock["now"]),
        (today - timedelta(days=1), stock["1_day_ago"]),
        (today - timedelta(days=7), stock["1_week_ago"]),
        (today - timedelta(days=30), stock["1_month_ago"]),
        (today - timedelta(days=365), stock["1_year_ago"]),
    ]

    for dt, value in data_points:
        date_str = f"{dt.year}/{dt.month}/{dt.day}"

        if date_str not in existing:
            ws.append_row([date_str, value])
            print(f"[ADD] Stock {date_str} = {value}")
        else:
            print(f"[SKIP] Stock {date_str} already exists")


# ------------------------------------------------------------
#  Crypto API（Alternative.me）
# ------------------------------------------------------------
def get_crypto_fgi():
    print("[INFO] Requesting Crypto FGI from alternative.me ...")
    data = requests.get("https://api.alternative.me/fng/?limit=30").json()["data"]

    print("[DATA] Crypto FGI received →", data[0])

    return {
        "now": int(data[0]["value"]),
        "1_day_ago": int(data[1]["value"]),
        "1_week_ago": int(data[7]["value"]),
        "1_month_ago": int(data[-1]["value"]),
        "raw": data,
    }


# ------------------------------------------------------------
#  Crypto 過去7日保存
# ------------------------------------------------------------
def append_last_7days_crypto(raw):
    print("[INFO] Adding last 7 days Crypto data...")
    ws = get_sheet("CryptoGreedFear")
    existing = {r[0] for r in ws.get_all_values()[1:]}

    for d in reversed(raw[:7]):
        dt = datetime.fromtimestamp(int(d["timestamp"]))
        date = f"{dt.year}/{dt.month}/{dt.day}"
        if date not in existing:
            ws.append_row([date, int(d["value"]), d["value_classification"]])
            print(f"[ADD] Crypto {date} = {d['value']}")
        else:
            print(f"[SKIP] Crypto {date} exists")


# ------------------------------------------------------------
# グラフ用データ（30件＋現在値）
# ------------------------------------------------------------
def get_last30_with_now(sheet_name, now_value):
    ws = get_sheet(sheet_name)
    rows = ws.get_all_values()[1:]

    vals = [int(float(r[1])) for r in rows[-29:]]
    vals.append(int(now_value))

    print(f"[INFO] Loaded {sheet_name} last 30 values (+now) → {vals}")
    return vals


# ------------------------------------------------------------
# 色
# ------------------------------------------------------------
def value_to_color(value):
    if value <= 24:  return "#FD5763"
    elif value <= 44: return "#FC854E"
    elif value <= 55: return "#FED236"
    elif value <= 75: return "#A1D778"
    return "#6BCA67"


# ------------------------------------------------------------
# ラベル
# ------------------------------------------------------------
def value_to_label(value):
    if value <= 24:  return "Extreme Fear"
    elif value <= 44: return "Fear"
    elif value <= 55: return "Neutral"
    elif value <= 75: return "Greed"
    return "Extreme Greed"


# ------------------------------------------------------------
# 値（Bold）
# ------------------------------------------------------------
def draw_text_dynamic(draw, xywh, text, font, value):
    x, y, w, h = xywh
    color = value_to_color(value)

    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text((x + (w - tw)/2, y + (h - th)/2), text, fill=color, font=font)


# ------------------------------------------------------------
# ラベル（Bold）
# ------------------------------------------------------------
def draw_label_under_value(draw, xywh, value, font_small):
    x, y, w, h = xywh
    label = value_to_label(value)
    color = value_to_color(value)

    tw, th = draw.textbbox((0, 0), label, font=font_small)[2:]
    draw.text((x + (w - tw)/2, y + h + 2),
              label,
              fill=color,
              font=font_small)


# ------------------------------------------------------------
# 針（直線のみ）
# ------------------------------------------------------------
def draw_fancy_needle(draw, center, value, length=200, color="#444444"):

    if value <= 24:
        angle = 180 + (value / 24) * (215 - 180)
    elif value <= 44:
        angle = 216 + ((value - 25) / (44 - 25)) * (251 - 216)
    elif value <= 55:
        angle = 252 + ((value - 45) / (55 - 45)) * (287 - 252)
    elif value <= 75:
        angle = 288 + ((value - 56) / (75 - 56)) * (323 - 288)
    else:
        angle = 324 + ((value - 76) / (100 - 76)) * (360 - 324)

    rad = math.radians(angle)
    x0, y0 = center
    x1 = x0 + length * math.cos(rad)
    y1 = y0 + length * math.sin(rad)

    draw.line((x0, y0, x1, y1), fill=color, width=6)


# ------------------------------------------------------------
# グラフ描画
# ------------------------------------------------------------
def draw_line_graph(draw, xywh, values, color, width=3, dot_color=None):
    x, y, w, h = xywh
    pts = []

    for i, v in enumerate(values):
        px = x + (i / (len(values)-1)) * w
        py = y + h - (v / 100) * h
        pts.append((px, py))

    draw.line(pts, fill=color, width=width)

    for (px, py) in pts:
        draw.ellipse((px-3, py-3, px+3, py+3), fill=dot_color or color)


# ------------------------------------------------------------
# 🚀 メイン処理（GitHub Actions 対応）
# ------------------------------------------------------------
def generate_image():

    print("\n===================== START generate.py =====================\n")

    # ---- データ取得 ----
    stock = get_stock_fgi()
    crypto = get_crypto_fgi()

    append_stock_history(stock)
    append_last_7days_crypto(crypto["raw"])

    crypto_one_year = get_crypto_one_year_ago()

    # ---- テンプレート画像 ----
    template = "template/FearGreedTemplate.png"   # ← GitHub に置く

    img = Image.open(template).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ---- フォント ----
    font_path = "noto-sans-jp/NotoSansJP-Bold.otf"

font       = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 40)
font_big   = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 70)
font_small = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 16)


    # ---- 座標 ----
    coords = {
        "stock": {
            "1_year_ago": [220,350,40,40],
            "1_month_ago":[220,423,40,40],
            "1_week_ago":[220,496,40,40],
            "1_day_ago":[220,570,40,40],
            "previous":[211,160,218,218],
        },
        "bitcoin":{
            "1_year_ago":[1060,350,40,40],
            "1_month_ago":[1060,423,40,40],
            "1_week_ago":[1060,496,40,40],
            "1_day_ago":[1060,570,40,40],
            "previous":[771,160,218,218],
        },
        "graph":[360,380,480,220]
    }

    # ---- 値・ラベル描画 ----
    for key in ["1_year_ago","1_month_ago","1_week_ago","1_day_ago"]:
        val = stock[key]
        draw_text_dynamic(draw, coords["stock"][key], str(val), font, val)
        draw_label_under_value(draw, coords["stock"][key], val, font_small)

    for key in ["1_year_ago","1_month_ago","1_week_ago","1_day_ago"]:
        val = crypto_one_year if key == "1_year_ago" else crypto[key]
        draw_text_dynamic(draw, coords["bitcoin"][key], str(val), font, val)
        draw_label_under_value(draw, coords["bitcoin"][key], val, font_small)

    # ---- 針 ----
    draw_fancy_needle(draw, (320, 324), stock["now"])
    draw_fancy_needle(draw, (880, 324), crypto["now"])

    # ---- current value（大きく） ----
    draw_text_dynamic(draw, coords["stock"]["previous"],
                      str(stock["now"]), font_big, stock["now"])

    draw_text_dynamic(draw, coords["bitcoin"]["previous"],
                      str(crypto["now"]), font_big, crypto["now"])

    # ---- グラフ ----
    gx, gy, gw, gh = coords["graph"]

    stock_vals  = get_last30_with_now("StockFear&Greed", stock["now"])
    crypto_vals = get_last30_with_now("CryptoGreedFear", crypto["now"])

    draw_line_graph(draw, (gx,gy,gw,gh), stock_vals,  "#f2f2f2", dot_color="#ffffff")
    draw_line_graph(draw, (gx,gy,gw,gh), crypto_vals, "#f7921a", dot_color="#f7921a")

    # ---- 保存 ----
    os.makedirs("output", exist_ok=True)
    output_path = "output/FearGreed_Output.png"

    img.save(output_path)

    print("\n[SAVED] →", output_path)
    print("\n===================== FINISHED generate.py =====================\n")

    return output_path
