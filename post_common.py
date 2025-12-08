# ================================
#  投稿文生成（共通モジュール）
# ================================
from datetime import datetime

def build_post_text():
    """
    画像生成後、X / Bluesky / Misskey すべてで使う投稿文を統一生成
    """
    today = datetime.now().strftime("%Y/%m/%d")

    text = (
        f"📊 Fear & Greed Index ({today})\n"
        f"\n"
        f"株式 & 仮想通貨の現在の市場心理をまとめました。\n"
        f"詳細は画像をご覧ください。\n"
        f"\n"
        f"#FearAndGreedIndex #Crypto #Stocks"
    )

    return text
