import urllib.request
import json
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONFIG_PATH = Path("config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config.get("telegram", {}).get("bot_token")
out_dir = Path("inputs/telegram_uploads")
out_dir.mkdir(parents=True, exist_ok=True)

print("Dang lang nghe va tai anh tu Telegram Bot (@Genvideo1_bot)...")
start_time = time.time()
offset = 0

while time.time() - start_time < 35:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=5&offset={offset}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            updates = data.get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                msg = u.get("message") or u.get("channel_post") or {}
                photos = msg.get("photo", [])
                doc = msg.get("document", {})
                caption = msg.get("caption", "")
                text = msg.get("text", "")
                uid = u["update_id"]

                if photos:
                    file_id = photos[-1]["file_id"]
                    with urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}") as fr:
                        finfo = json.loads(fr.read().decode())
                        fpath = finfo["result"]["file_path"]
                        ext = Path(fpath).suffix or ".jpg"
                        dest = out_dir / f"tg_photo_{uid}{ext}"
                        with urllib.request.urlopen(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fpath}") as dr, open(dest, "wb") as out:
                            out.write(dr.read())
                        print(f"SUCCESS: Da tai thanh cong anh: {dest} ({dest.stat().st_size} bytes)")
                        if caption:
                            print(f"Caption: {caption}")
                        sys.exit(0)

                elif doc:
                    file_id = doc["file_id"]
                    fname = doc.get("file_name", f"tg_doc_{uid}")
                    with urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}") as fr:
                        finfo = json.loads(fr.read().decode())
                        fpath = finfo["result"]["file_path"]
                        dest = out_dir / fname
                        with urllib.request.urlopen(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fpath}") as dr, open(dest, "wb") as out:
                            out.write(dr.read())
                        print(f"SUCCESS: Da tai thanh cong tep: {dest} ({dest.stat().st_size} bytes)")
                        sys.exit(0)

                elif text:
                    print(f"Nhan tin nhan text: {text}")

    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(1)

print("Het thoi gian cho (Timeout 35s). Chua thay anh moi gui.")
