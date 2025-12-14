# ==========================================
# post_x.py（スプラ方式・最終版）
# ==========================================
import os
import sys
import tweepy

# ======================================================
# 認証情報
# ======================================================
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

IMAGE_PATH = os.getenv("IMAGE_PATH")

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print("[ERROR] Twitter API credentials が不足しています")
    sys.exit(1)

if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
    print("[ERROR] 画像が見つかりません →", IMAGE_PATH)
    sys.exit(1)

# ======================================================
# 投稿文（固定 or 生成済みを使う）
# ======================================================
def build_post_text():
    # ※ generate.py 側で内容は確定している前提
    return "CNN・Crypto Fear & Greed Index\n#FearAndGreed #Bitcoin"

# ======================================================
# X 投稿処理
# ======================================================
def upload_media_v1(image_path):
    auth = tweepy.OAuth1UserHandler(
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET
    )
    api = tweepy.API(auth)
    media = api.media_upload(filename=image_path)
    print(f"[INFO] Media uploaded → media_id={media.media_id}")
    return str(media.media_id)

def post_tweet_v2(text, media_id):
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    response = client.create_tweet(
        text=text,
        media_ids=[media_id]
    )
    tweet_id = response.data["id"]
    print(f"[SUCCESS] 投稿完了 → tweet_id={tweet_id}")

# ======================================================
# MAIN
# ======================================================
def main():
    print("[INFO] post_x.py started")

    text = build_post_text()
    media_id = upload_media_v1(IMAGE_PATH)
    post_tweet_v2(text, media_id)

    print("[DONE] X 投稿完了")

if __name__ == "__main__":
    main()
