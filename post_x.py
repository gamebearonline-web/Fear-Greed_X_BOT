# ==========================================
# post_x.py（スプラ方式・最終確定版）
# ==========================================
import os
import sys
import tweepy

# ======================================================
# 環境変数
# ======================================================
API_KEY        = os.getenv("TWITTER_API_KEY")
API_SECRET     = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN   = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET  = os.getenv("TWITTER_ACCESS_SECRET")

IMAGE_PATH     = os.getenv("IMAGE_PATH", "fgi-image/FearGreed_Output.png")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH", "fgi-image/post_text.txt")

# ======================================================
# バリデーション
# ======================================================
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print("[ERROR] Twitter API credentials が不足しています")
    sys.exit(1)

if not os.path.exists(IMAGE_PATH):
    print("[ERROR] 画像が見つかりません →", IMAGE_PATH)
    sys.exit(1)

if not os.path.exists(POST_TEXT_PATH):
    print("[ERROR] 投稿文が見つかりません →", POST_TEXT_PATH)
    sys.exit(1)

# ======================================================
# 投稿文読み込み（generate.py 生成物）
# ======================================================
def load_post_text():
    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

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

    text = load_post_text()

    print("----- POST TEXT (X) -----")
    print(text)

    media_id = upload_media_v1(IMAGE_PATH)
    post_tweet_v2(text, media_id)

    print("[DONE] X 投稿完了")

if __name__ == "__main__":
    main()
