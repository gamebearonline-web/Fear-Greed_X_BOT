# ======================================
#  Fear & Greed Index 画像生成（安定版）
#  ※ RapidAPI 仕様変更対応 / 例外強化
# ======================================

from PIL import Image, ImageDraw, ImageFont
import requests
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import math

# ======================================
#  Google Sheets 認証
# ======================================
def get_sheet(sheet_name):
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

# ======================================
# Crypto：1年前データ取得
# ======================================
def get_crypto_one_year_ago():
    ws = get_sheet("CryptoGreedFear")

    d = datetime.now() - timedelta(days=365)
    target = f"{d.year}/{d.month}/{d.day}"

    rows = ws.get_all_values()
    for r in rows[1:]:
        if r[0] == target:
            return int(r[1])
    return None

# ======================================
# RapidAPI：株式 Fear & Greed（安全版）
# ======================================
def get_stock_fgi():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    res = requests.get(url, headers=headers)
    try:
        data = res.json()
    except Exception:
        print("[ERROR] RapidAPI Decode:", res.text)
        raise

    # 旧仕様 or 新仕様
    if "fgi" in data:
        fgi = data["fgi"]
    elif "data" in data:
        fgi = data["data"]
    else:
        raise Exception(f"[ERROR] FGI 構造エラー: {data}")

    return {
        "now":          int(fgi["now"]["value"]),
        "1_day_ago":    int(fgi["previousClose"]["value"]),
        "1_week_ago":   int(fgi["oneWeekAgo"]["value"]),
        "1_month_ago":  int(fgi["oneMonthAgo"]["value"]),
        "1_year_ago":   int(fgi["oneYearAgo"]["value"]),
        "raw": fgi,
    }

# ======================================
# Stock FGI 履歴追加
# ======================================
def append_stock_history(stock):
    ws = get_sheet("StockFear&Greed")

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

# ======================================
# Crypto API
# ======================================
def get_crypto_fgi():
    data = requests.get("https://api.alternative.me/fng/?limit=30").json()["data"]

    return {
        "now": int(data[0]["value"]),
        "1_day_ago": int(data[1]["value"]),
        "1_week_ago": int(data[7]["value"]),
        "1_month_ago": int(data[-1]["value"]),
        "raw": data,
    }

# ======================================
# Crypto 過去7日履歴
# ======================================
def append_last_7days_crypto(raw):
    ws = get_sheet("CryptoGreedFear")
    existing = {r[0] for r in ws.get_all_values()[1:]}

    for d in reversed(raw[:7]):
        dt = datetime.fromtimestamp(int(d["timestamp"]))
        date = f"{dt.year}/{dt.month}/{dt.day}"
        if date not in existing:
            ws.append_row([date, int(d["value"]), d["value_classification"]])

# ======================================
# グラフ用データ
# ======================================
def get_last30_with_now(sheet_name, now_value):
    ws = get_sheet(sheet_name)
    rows = ws.get_all_values()[1:]

    vals = [int(float(r[1])) for r in rows[-29:]]
    vals.append(int(now_value))
    return vals

# ======================================
# 色
# ======================================
def value_to_color(value):
    if value <= 24:  return "#FD5763"
    elif value <= 44: return "#FC854E"
    elif value <= 55: return "#FED236"
    elif value <= 75: return "#A1D778"
    return "#6BCA67"

def value_to_label(value):
    if value <= 24:  return "Extreme Fear"
    if value <= 44:  return "Fear"
    if value <= 55:  return "Neutral"
    if value <= 75:  return "Greed"
    return "Extreme Greed"

# ======================================
# 文字描画
# ======================================
def draw_text_center(draw, xywh, text, font, color):
    x, y, w, h = xywh
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text((x+(w-tw)/2, y+(h-th)/2), text, font=font, fill=color)

def draw_label(draw, xywh, value, font):
    label = value_to_label(value)
    x,y,w,h = xywh
    tw, th = draw.textbbox((0,0), label, font=font)[2:]
    draw.text((x+(w-tw)/2, y+h), label, font=font, fill=value_to_color(value))

# ======================================
# 針描画
# ======================================
def draw_needle(draw, center, value, length=200):
    if value <= 24:
        angle = 180 + (value / 24) * 35
    elif value <= 44:
        angle = 216 + ((value - 25) / 19) * 35
    elif value <= 55:
        angle = 252 + ((value - 45) / 10) * 35
    elif value <= 75:
        angle = 288 + ((value - 56) / 19) * 35
    else:
        angle = 324 + ((value - 76) / 24) * 36

    rad = math.radians(angle)
    x0,y0 = center
    x1 = x0 + length * math.cos(rad)
    y1 = y0 + length * math.sin(rad)

    draw.line((x0,y0,x1,y1), fill="#444444", width=6)

# ======================================
# 折れ線グラフ
# ======================================
def draw_line(draw, xywh, values, color, dot):
    x,y,w,h = xywh
    pts = []
    for i,v in enumerate(values):
        px = x + (i/(len(values)-1))*w
        py = y + h - (v/100)*h
        pts.append((px,py))

    draw.line(pts, fill=color, width=3)
    for px,py in pts:
        draw.ellipse((px-3,py-3,px+3,py+3), fill=dot)

# ======================================
# 日付描画
# ======================================
def draw_date(draw):
    today = datetime.now()
    week_jp = ["月","火","水","木","金","土","日"]
    date_text = today.strftime("%Y/%m/%d") + f"（{week_jp[today.weekday()]}）"
    font_date = ImageFont.truetype("noto-sans-jp/NotoSansJP-Regular.otf", 20)

    x,y,w,h = 1020, 15, 140, 20
    tw, th = draw.textbbox((0,0), date_text, font=font_date)[2:]
    draw.text((x+(w-tw)/2, y+(h-th)/2), date_text, font=font_date, fill="#4D4D4D")

# ======================================
# 画像生成メイン
# ======================================
def generate_image():

    stock = get_stock_fgi()
    crypto = get_crypto_fgi()

    append_stock_history(stock)
    append_last_7days_crypto(crypto["raw"])

    crypto_one_year = get_crypto_one_year_ago()

    img = Image.open("template/FearGreedTemplate.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    font       = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 40)
    font_big   = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 70)
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

    # STOCK
    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = stock[k]
        draw_text_center(draw, coords["stock"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["stock"][k], v, font_small)

    # CRYPTO
    for k in ["1_day_ago","1_week_ago","1_month_ago","1_year_ago"]:
        v = crypto_one_year if k=="1_year_ago" else crypto[k]
        draw_text_center(draw, coords["crypto"][k], str(v), font, value_to_color(v))
        draw_label(draw, coords["crypto"][k], v, font_small)

    # 針
    draw_needle(draw, (320, 324), stock["now"])
    draw_needle(draw, (880, 324), crypto["now"])

    # 中央数値
    draw_text_center(draw, coords["stock"]["previous"], str(stock["now"]), font_big, value_to_color(stock["now"]))
    draw_text_center(draw, coords["crypto"]["previous"], str(crypto["now"]), font_big, value_to_color(crypto["now"]))

    # グラフ
    gx,gy,gw,gh = coords["graph"]
    draw_line(draw, (gx,gy,gw,gh), get_last30_with_now("StockFear&Greed", stock["now"]), "#f2f2f2", "#ffffff")
    draw_line(draw, (gx,gy,gw,gh), get_last30_with_now("CryptoGreedFear", crypto["now"]), "#f7921a", "#f7921a")

    # 日付
    draw_date(draw)

    # 保存
    os.makedirs("output", exist_ok=True)
    path = "output/FearGreed_Output.png"
    img.save(path)
    print("[SAVED]", path)

    return path

# ======================================
# MAIN
# ======================================
if __name__ == "__main__":
    generate_image()
