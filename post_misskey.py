import os
import requests

MISSKEY_HOST = os.getenv("MISSKEY_HOST")
MISSKEY_TOKEN = os.getenv("MISSKEY_TOKEN")
IMAGE_PATH = os.getenv("IMAGE_PATH")
POST_TEXT_PATH = os.getenv("POST_TEXT_PATH")  # post_text.txt のパス

def normalize_host(url: str) -> str:
    """末尾の / を削除して正規化"""
    if url.endswith("/"):
        return url[:-1]
    return url

def load_post_text():
    """X 投稿用に生成した文章を読み込む"""
    if not POST_TEXT_PATH or not os.path.exists(POST_TEXT_PATH):
        raise Exception(f"[ERROR] POST_TEXT_PATH が存在しません → {POST_TEXT_PATH}")

    with open(POST_TEXT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def upload_file():
    """Misskey に画像をアップロードして fileId を得る"""
    url = f"{MISSKEY_HOST}/api/drive/files/create"

    try:
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": f}
            data = {"i": MISSKEY_TOKEN}
            r = requests.post(url, data=data, files=files)

    except Exception as e:
        raise Exception(f"[ERROR] Misskey ファイルアップロード時エラー: {e}")

    if r.status_code != 200:
        raise Exception(f"[ERROR] Misskey ファイルアップロード失敗: {r.text}")

    # JSON パース確認
    try:
        file_id = r.json().get("id")
    except Exception:
        raise Exception("[ERROR] Misskey 応答が JSON ではありません: " + r.text)

    if not file_id:
        raise Exception("[ERROR] file_id が取得できません: " + r.text)

    print(f"[OK] Misskey file uploaded → file_id={file_id}")
    return file_id

def main():
    print("[INFO] post_misskey.py started")

    if not MISSKEY_HOST or not MISSKEY_TOKEN:
        raise Exception("[ERROR] MISSKEY_HOST / MISSKEY_TOKEN が設定されていません")

    if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
        raise Exception(f"[ERROR] IMAGE_PATH が存在しません → {IMAGE_PATH}")

    # URL を正規化（最後の / を削除）
    globals()["MISSKEY_HOST"] = normalize_host(MISSKEY_HOST)

    # X の投稿文を artifact から読み込む
    text = load_post_text()
    print("\n--- POST TEXT (Misskey) ---\n" + text + "\n")

    # 画像アップロード
    file_id = upload_file()

    # 投稿本体
    note_url = f"{MISSKEY_HOST}/api/notes/create"
    payload = {
        "i": MISSKEY_TOKEN,
        "text": text,
        "fileIds": [file_id],
    }

    try:
        r = requests.post(note_url, json=payload)
    except Exception as e:
        raise Exception(f"[ERROR] Misskey 投稿時エラー: {e}")

    print("Post status:", r.status_code)
    print("Response:", r.text)

    if r.status_code != 200:
        raise Exception("[ERROR] Misskey 投稿失敗: " + r.text)

    print("[OK] Posted to Misskey successfully!")

if __name__ == "__main__":
    main()
