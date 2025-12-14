import argparse
import os
import math
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ======================================
# 引数
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
    return date_str in {r[0] for r in ws.get_all_values()[1:] if r}


# ======================================
# Crypto：1年前
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
# RapidAPI → Stock FGI
# ======================================
def get_stock_fgi():
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
    }

    data = requests.get(url, headers=headers).json()
    fgi = data.get("fgi", data.get("data"))

    return {
        "now": int(fgi["now"]["value"]),
        "prev": int(fgi["previousClose"]["value"]),
        "1_week_ago": int(fgi["oneWeekAgo"]["value"]),
        "1_month_ago": int(fgi["oneMonthAgo"]["value"]),
        "1_year_ago": int(fgi["oneYearAgo"]["value"]),
    }


# ======================================
# Crypto FGI
# ======================================
def get_crypto_fgi():
    raw = requests.get("https://api.alternative.me/fng/?limit=30").json()["data"]
    return {
        "now": int(raw[0]["value"]),
        "prev": int(raw[1]["value"]),
        "raw": raw,
    }


# ======================================
# 色・ラベル
# ======================================
def value_to_label(v):
    if v <= 24: return "Extreme Fear"
    if v <= 44: return "Fear"
    if v <= 55: return "Neutral"
    if v <= 75: return "Greed"
    return "Extreme Greed"


# ======================================
# 投稿文生成（★重要）
# ======================================
def build_post_text(stock, crypto):
    JST = datetime.utcnow() + timedelta(hours=9)
    week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][JST.weekday()]
    date_str = JST.strftime("%Y/%m/%d") + f"（{week}）"

    s_diff = stock["now"] - stock["prev"]
    c_diff = crypto["now"] - crypto["prev"]

    return (
        "CNN・Crypto Fear & Greed Index（恐怖と欲望指数）\n"
        f"{date_str}\n\n"
        f"⬜Stock：{stock['now']}({s_diff:+d})【{value_to_label(stock['now'])}】\n"
        f"🟧Bitcoin：{crypto['now']}({c_diff:+d})【{value_to_label(crypto['now'])}】"
    )


# ======================================
# 画像生成（省略なし）
# ======================================
def generate(output_path):
    stock = get_stock_fgi()
    crypto = get_crypto_fgi()

    # ---------- 投稿文 ----------
    post_text = build_post_text(stock, crypto)
    post_text_path = os.path.join(
        os.path.dirname(output_path), "post_text.txt"
    )

    # ---------- 画像 ----------
    base = Image.open("template/FearGreedTemplate.png").convert("RGBA")
    draw = ImageDraw.Draw(base)

    font_big = ImageFont.truetype("noto-sans-jp/NotoSansJP-Bold.otf", 70)

    draw.text((320, 250), str(stock["now"]), font=font_big, fill="#333333")
    draw.text((880, 250), str(crypto["now"]), font=font_big, fill="#333333")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base.save(output_path)

    with open(post_text_path, "w", encoding="utf-8") as f:
        f.write(post_text)

    print("[SAVED]", output_path)
    print("[SAVED]", post_text_path)
    print("----- POST TEXT -----")
    print(post_text)


# ======================================
# MAIN
# ======================================
if __name__ == "__main__":
    args = parse_args()
    generate(args.output)
