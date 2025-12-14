import argparse
import os
import math
import requests
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


def sheet_has_date(ws, date_str):
    """A列に date_str (YYYY/MM/DD) が存在するか"""
    return date_str in {r[0] for r in ws.get_all_values()[1:] if r}


# ======================================
# Crypto：1年前の値（JST）
# ======================================
def get_crypto_one_year_ago():
    ws = get_sheet("CryptoGreedFear")
    JST = datetime.utcnow() + timedelta(hours=9)
    target = (JST - timedelta(days=365)).strftime("%Y/%m/%d")

    for r in ws.get_all_values()[1:]:
        if r and r[0] == target:
            return int(r[1])
    return None

# ======================================
# 投稿文生成（画像とは独立）
# ======================================
def build_post_text(stock, crypto):
    JST = datetime.utcnow() + timedelta(hours=9)
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][JST.weekday()]
    date_text = JST.strftime("%Y/%m/%d") + f"（{weekday}）"

    def diff(now, prev):
        d = now - prev
        if d > 0:
            return f"(+{d})"
        if d < 0:
            return f"({d})"
        return "(±0)"

    return (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{date_text}\n\n"
        f"⬜Stock：{stock['now']}{diff(stock['now'], stock['1_day_ago'])}"
        f"【{value_to_label(stock['now'])}】\n"
        f"🟧Bitcoin：{crypto['now']}{diff(crypto['now'], crypto['1_day_ago'])}"
        f"【{value_to_label(crypto['now'])}】"
    )



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
        "now":         int(fgi["now"]["value"]),
        "1_day_ago":   int(fgi["previousClose"]["value"]),
        "1_week_ago":  int(fgi["oneWeekAgo"]["value"]),
        "1_month_ago": int(fgi["oneMonthAgo"]["value"]),
        "1_year_ago":  int(fgi["oneYearAgo"]["value"]),
    }


# ======================================
# Stock FGI → 履歴追記（土日スキップ + 日付重複防止）
# ======================================
def append_stock_history(stock):
    ws = get_sheet("StockFear&Greed")

    JST = datetime.utcnow() + timedelta(hours=9)
    weekday = JST.weekday()  # 月=0 ... 日=6

    if weekday >= 5:
        print("[SKIP] Weekend → StockFear&Greed")
        return

    today_str = JST.strftime("%Y/%m/%d")

    # ★ 今日が既にあるなら完全スキップ
    if sheet_has_date(ws, today_str):
        print(f"[SKIP] StockFear&Greed {today_str} already exists")
        return

    points = [
        (JST,                       stock["now"]),
        (JST - timedelta(days=1),   stock["1_day_ago"]),
        (JST - timedelta(days=7),   stock["1_week_ago"]),
        (JST - timedelta(days=30),  stock["1_month_ago"]),
        (JST - timedelta(days=365), stock["1_year_ago"]),
    ]

    for dt, v in points:
        d = dt.strftime("%Y/%m/%d")
        if not sheet_has_date(ws, d):
            ws.append_row([d, v])
            print(f"[ADD] StockFear&Greed → {d}: {v}")


# ======================================
# Crypto FGI API
# ======================================
def get_crypto_fgi():
    raw = requests.get("https://api.alternative.me/fng/?limit=30").json()["data"]
    return {
        "now":         int(raw[0]["value"]),
        "1_day_ago":   int(raw[1]["value"]),
        "1_week_ago":  int(raw[7]["value"]),
        "1_month_ago": int(raw[-1]["value"]),
        "raw": raw,
    }


# ======================================
# Crypto 履歴追記（日付重複防止）
# ======================================
def append_last_7days_crypto(raw):
    ws = get_sheet("CryptoGreedFear")

    for d in reversed(raw[:7]):
        dt = datetime.fromtimestamp(int(d["timestamp"])) + timedelta(hours=9)
        date_str = dt.strftime("%Y/%m/%d")

        if sheet_has_date(ws, date_str):
            print(f"[SKIP] CryptoGreedFear {date_str}")
            continue

        ws.append_row([date_str, int(d["value"]), d["value_classification"]])
        print(f"[ADD] CryptoGreedFear → {date_str}: {int(d['value'])}")


# ======================================
# グラフ用データ（29 + 今日）
# ======================================
def get_last30_with_now(sheet, now_value):
    ws = get_sheet(sheet)
    vals = [int(float(r[1])) for r in ws.get_all_values()[1:][-29:] if r]
    vals.append(int(now_value))
    return vals


# ======================================
# 色・ラベル
# ======================================
def value_to_color(v):
    if v <= 24: return "#FD5763"
    if v <= 44: return "#FC854E"
    if v <= 55: return "#FED236"
    if v <= 75: return "#A1D778"
    return "#6BCA67"

def value_to_label(v):
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 55: return "Neutral"
    if v <= 75: return "Greed"
    return "Extreme Greed"


# ======================================
# 描画ユーティリティ
# ======================================
def draw_text_center(draw, box, text, font, color):
    x,y,w,h = box
    tw,th = draw.textbbox((0,0), text, font=font)[2:]
    draw.text((x+(w-tw)/2, y+(h-th)/2), text, font=font, fill=color)

def draw_label(draw, box, value, font):
    label = value_to_label(value)
    x,y,w,h = box
    tw,th = draw.textbbox((0,0), label, font=font)[2:]
    draw.text((x+(w-tw)/2, y+h), label, font=font, fill=value_to_color(value))


def draw_needle(draw, center, value, length=200):
    if value <= 24: angle = 180 + (value/24)*35
    elif value <= 44: angle = 216 + ((value-25)/19)*35
    elif value <= 55: angle = 252 + ((value-45)/10)*35
    elif value <= 75: angle = 288 + ((value-56)/19)*35
    else: angle = 324 + ((value-76)/24)*36

    rad = math.radians(angle)
    x0,y0 = center
    x1 = x0 + length * math.cos(rad)
    y1 = y0 + length * math.sin(rad)
    draw.line((x0,y0,x1,y1), fill="#444444", width=6)


def draw_line(draw, box, values, color, dot):
    x,y,w,h = box
    pts = [(x+(i/(len(values)-1))*w, y+h-(v/100)*h) for i,v in enumerate(values)]
    draw.line(pts, fill=color, width=3)
    for px,py in pts:
        draw.ellipse((px-3,py-3,px+3,py+3), fill=dot)


def draw_date(draw):
    JST = datetime.utcnow() + timedelta(hours=9)
    week = "月火水木金土日"[JST.weekday()]
    text = JST.strftime("%Y/%m/%d") + f"（{week}）"
    font = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 20)
    x,y,w,h = 1020,15,140,20
    tw,th = draw.textbbox((0,0), text, font=font)[2:]
    draw.text((x+(w-tw)/2, y+(h-th)/2), text, font=font, fill="#4D4D4D")


# ======================================
# 画像生成
# ======================================
def generate(output_path):
    stock = get_stock_fgi()
    crypto = get_crypto_fgi()
    crypto_1y = get_crypto_one_year_ago()

    append_stock_history(stock)
    append_last_7days_crypto(crypto["raw"])

    base = Image.open("template/FearGreedTemplate.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    font = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 40)
    font_big = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 70)
    font_small = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 16)

    coords = {
        "stock": {
            "1_day_ago":[220,350,40,40],
            "1_week_ago":[220,423,40,40],
            "1_month_ago":[220,496,40,40],
            "1_year_ago":[220,570,40,40],
            "previous":[211,160,218,218],
        },
        "crypto": {
            "1_day_ago":[1060,350,40,40],
            "1_week_ago":[1060,423,40,40],
            "1_month_ago":[1060,496,40,40],
            "1_year_ago":[1060,570,40,40],
            "previous":[771,160,218,218],
        },
        "graph":[360,380,480,220]
    }

    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = stock[k]
        draw_text_center(draw, coords["stock"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["stock"][k], v, font_small)

    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = crypto_1y if k=="1_year_ago" else crypto[k]
        draw_text_center(draw, coords["crypto"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["crypto"][k], v, font_small)

    draw_needle(draw, (320,324), stock["now"])
    draw_needle(draw, (880,324), crypto["now"])

    draw_text_center(draw, coords["stock"]["previous"], str(stock["now"]), font_big, value_to_color(stock["now"]))
    draw_text_center(draw, coords["crypto"]["previous"], str(crypto["now"]), font_big, value_to_color(crypto["now"]))

    x,y,w,h = coords["graph"]
    draw_line(draw, (x,y,w,h), get_last30_with_now("StockFear&Greed", stock["now"]), "#f2f2f2", "#ffffff")
    draw_line(draw, (x,y,w,h), get_last30_with_now("CryptoGreedFear", crypto["now"]), "#f7921a", "#f7921a")

    draw_date(draw)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base.save(output_path)
    print("[SAVED]", output_path)


    # ------------------------------
    # 投稿文を書き出す（★追加）
    # ------------------------------
    post_text = build_post_text(stock, crypto)
    with open(
        os.path.join(os.path.dirname(output_path), "post_text.txt"),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(post_text)



# ======================================
# MAIN
# ======================================
if __name__ == "__main__":
    args = parse_args()
    generate(args.output)


