# ==========================================
# post_bluesky.py（atproto 0.0.65 対応確定版）
#  - upload_blob() で画像アップロード
#  - com.atproto.repo.create_record で images embed を自前で組む
# ==========================================
import os
from datetime import datetime, timezone

from atproto import Client
from atproto import models


BSKY_HANDLE = os.getenv("BSKY_HANDLE")
BSKY_APP_PASSWORD = os.getenv("BSKY_APP_PASSWORD")
IMAGE_PATH = os.getenv("IMAGE_PATH")

if not BSKY_HANDLE or not BSKY_APP_PASSWORD:
    raise Exception("[ERROR] Bluesky の認証情報が不足しています")

if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
    raise Exception(f"[ERROR] 画像が存在しません → {IMAGE_PATH}")

POST_TEXT = "CNN・Crypto Fear & Greed Index\n#FearAndGreed #Bitcoin"


def main():
    print("[INFO] Starting Bluesky posting...")
    print("\n----- POST TEXT (Bluesky) -----\n" + POST_TEXT + "\n")

    client = Client()
    client.login(BSKY_HANDLE, BSKY_APP_PASSWORD)
    print("[INFO] Bluesky Login OK")

    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    # 画像アップロード（encoding 引数は渡さない）
    blob = client.upload_blob(img_bytes)
    # blob は atproto の BlobRef 形式（dictライク）で返る

    # images embed を組む（models を使用）
    embed = models.AppBskyEmbedImages.Main(
        images=[
            models.AppBskyEmbedImages.Image(
                image=blob.blob,   # ← ここが重要：blob全体ではなく blob.blob
                alt="Fear & Greed Index"
            )
        ]
    )

    # 投稿レコードを作って create_record
    record = models.AppBskyFeedPost.Record(
        text=POST_TEXT,
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        embed=embed
    )

    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,
            collection="app.bsky.feed.post",
            record=record
        )
    )

    print("[SUCCESS] 投稿完了（Bluesky）")


if __name__ == "__main__":
    main()
