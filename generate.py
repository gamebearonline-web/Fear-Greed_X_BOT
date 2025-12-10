import argparse
import os
import math
import requests
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ======================================
# 引数 (--output)
# ======================================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=str,
        default="output/FearGreed_Output.png",
        help="Output image path"
    )
    return parser.parse_args()


# ======================================
# Google Sheets
# ======================================
SHEET_ID = "1YS3tyCuduXf9SDhbgEOv74f5RHSapa8kBw5y979EYO0"

def get_sheet(sheet_name):
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


# ======================================
# Crypto：1年前の値
# ======================================
def get_crypto_one_year_ago():
    ws = get_sheet("CryptoGreedFear")
    target = (datetime.now() - timedelta(days=365)).strftime("%Y/%m/%d")

    for r in ws.get_all_values()[1:]:
        if r[0] == target:
            return int(r[1])
    return None


# ======================================
# RapidAPI → Stock FGI
# ======================================
def get_stock_fgi():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    res = requests.get(url, headers=headers)
    data = res.json()

    fgi = data.get("fgi", data.get("data"))

    return {
        "now":          int(fgi["now"]["value"]),
        "1_day_ago":    int(fgi["previousClose"]["value"]),
        "1_week_ago":   int(fgi["oneWeekAgo"]["value"]),
        "1_month_ago":  int(fgi["oneMonthAgo"]["value"]),
        "1_year_ago":   int(fgi["oneYearAgo"]["value"]),
        "raw": fgi,
    }


# ======================================
# Stock FGI → 履歴追記
# ======================================
def append_stock_history(stock):
    ws = get_sheet("StockFear&Greed")
    exist = {r[0] for r in ws.get_all_values()[1:]}
    today = datetime.now()

    points = [
        (today,                     stock["now"]),
        (today - timedelta(days=1), stock["1_day_ago"]),
        (today - timedelta(days=7), stock["1_week_ago"]),
        (today - timedelta(days=30), stock["1_month_ago"]),
        (today - timedelta(days=365), stock["1_year_ago"]),
    ]

    for dt, v in points:
        d = dt.strftime("%Y/%m/%d")
        if d not in exist:
            ws.append_row([d, v])


# ======================================
# Crypto FGI API
# ======================================
def get_crypto_fgi():
    raw = requests.get("https://api.alternative.me/fng/?limit=30").json()["data"]
    return {
        "now": int(raw[0]["value"]),
        "1_day_ago": int(raw[1]["value"]),
        "1_week_ago": int(raw[7]["value"]),
        "1_month_ago": int(raw[-1]["value"]),
        "raw": raw,
    }


# ======================================
# Crypto 履歴追記
# ======================================
def append_last_7days_crypto(raw):
    ws = get_sheet("CryptoGreedFear")
    exist = {r[0] for r in ws.get_all_values()[1:]}

    for d in reversed(raw[:7]):
        dt = datetime.fromtimestamp(int(d["timestamp"]))
        date = dt.strftime("%Y/%m/%d")
        if date not in exist:
            ws.append_row([date, int(d["value"]), d["value_classification"]])


# ======================================
# グラフ用データ
# ======================================
def get_last30_with_now(sheet, now_value):
    ws = get_sheet(sheet)
    vals = [int(float(r[1])) for r in ws.get_all_values()[1:][-29:]]
    vals.append(int(now_value))
    return vals


# --------------------------------------
# 色判定
# --------------------------------------
def value_to_color(v):
    if v <= 24:  return "#FD5763"
    if v <= 44:  return "#FC854E"
    if v <= 55:  return "#FED236"
    if v <= 75:  return "#A1D778"
    return "#6BCA67"


def value_to_label(v):
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 55: return "Neutral"
    if v <= 75: return "Greed"
    return "Extreme Greed"


# --------------------------------------
# 描画ユーティリティ
# --------------------------------------
def draw_text_center(draw, box, text, font, color):
    x, y, w, h = box
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text((x + (w - tw)/2, y + (h - th)/2), text, font=font, fill=color)


def draw_label(draw, box, value, font):
    label = value_to_label(value)
    x,y,w,h = box
    tw, th = draw.textbbox((0,0), label, font=font)[2:]
    draw.text((x+(w-tw)/2, y+h), label, font=font, fill=value_to_color(value))


# --------------------------------------
# 針
# --------------------------------------
def draw_needle(draw, center, value, length=200):
    v = value
    if v <= 24: angle = 180 + (v/24)*35
    elif v <= 44: angle = 216 + ((v-25)/19)*35
    elif v <= 55: angle = 252 + ((v-45)/10)*35
    elif v <= 75: angle = 288 + ((v-56)/19)*35
    else: angle = 324 + ((v-76)/24)*36

    rad = math.radians(angle)
    x0,y0 = center
    x1 = x0 + length * math.cos(rad)
    y1 = y0 + length * math.sin(rad)

    draw.line((x0,y0,x1,y1), fill="#444444", width=6)


# --------------------------------------
# 折れ線
# --------------------------------------
def draw_line(draw, box, values, color, dot):
    x,y,w,h = box
    pts = []
    for i,v in enumerate(values):
        px = x + (i/(len(values)-1))*w
        py = y + h - (v/100)*h
        pts.append((px,py))

    draw.line(pts, fill=color, width=3)
    for px,py in pts:
        draw.ellipse((px-3,py-3,px+3,py+3), fill=dot)


# --------------------------------------
# 日付
# --------------------------------------
def draw_date(draw):
    today = datetime.now()
    week = "月火水木金土日"[today.weekday()]
    text = today.strftime("%Y/%m/%d") + f"（{week}）"
    font = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 20)

    x,y,w,h = 1020, 15, 140, 20
    tw, th = draw.textbbox((0,0), text, font=font)[2:]
    draw.text((x+(w-tw)/2, y+(h-th)/2), text, font=font, fill="#4D4D4D")


# ======================================
# ★ 画像生成（スプラ式）
# ======================================
def generate(output_path):

    # ---- データ取得 ----
    stock = get_stock_fgi()
    crypto = get_crypto_fgi()
    crypto_1y = get_crypto_one_year_ago()

    append_stock_history(stock)
    append_last_7days_crypto(crypto["raw"])

    # ---- テンプレート読込（毎回新規 → 古い内容が残らない） ----
    base = Image.open("template/FearGreedTemplate.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    # ---- フォント読込 ----
    font = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 40)
    font_big = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 70)
    font_small = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 16)

    coords = {
        "stock": {
            "1_day_ago":   [220,350,40,40],
            "1_week_ago":  [220,423,40,40],
            "1_month_ago": [220,496,40,40],
            "1_year_ago":  [220,570,40,40],
            "previous":    [211,160,218,218],
        },
        "crypto": {
            "1_day_ago":   [1060,350,40,40],
            "1_week_ago":  [1060,423,40,40],
            "1_month_ago": [1060,496,40,40],
            "1_year_ago":  [1060,570,40,40],
            "previous":    [771,160,218,218],
        },
        "graph":[360,380,480,220]
    }

    # ---- Stock ----
    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = stock[k]
        draw_text_center(draw, coords["stock"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["stock"][k], v, font_small)

    # ---- Crypto ----
    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = crypto_1y if k == "1_year_ago" else crypto[k]
        draw_text_center(draw, coords["crypto"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["crypto"][k], v, font_small)

    # ---- 針 ----
    draw_needle(draw, (320, 324), stock["now"])
    draw_needle(draw, (880, 324), crypto["now"])

    # ---- 中央値 ----
    draw_text_center(draw, coords["stock"]["previous"], str(stock["now"]), font_big, value_to_color(stock["now"]))
    draw_text_center(draw, coords["crypto"]["previous"], str(crypto["now"]), font_big, value_to_color(crypto["now"]))

    # ---- グラフ ----
    x,y,w,h = coords["graph"]
    draw_line(draw, (x,y,w,h), get_last30_with_now("StockFear&Greed", stock["now"]), "#f2f2f2", "#ffffff")
    draw_line(draw, (x,y,w,h), get_last30_with_now("CryptoGreedFear", crypto["now"]), "#f7921a", "#f7921a")

    # ---- 日付 ----
    draw_date(draw)

    # ---- 保存 ----
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base.save(output_path)
    print("[SAVED]", output_path)


# ======================================
# MAIN（スプラ方式）
# ======================================
if __name__ == "__main__":
    args = parse_args()
    generate(args.output)
