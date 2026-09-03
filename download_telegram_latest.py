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
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

print(f"Connecting to Telegram Bot (@Genvideo1_bot)...")

# Long poll for updates up to 10 seconds
try:
    url = f"{TELEGRAM_API}/getUpdates?timeout=10&limit=50"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        updates = data.get("result", [])
        print(f"Total updates found: {len(updates)}")

        saved_files = []
        out_dir = Path("inputs/telegram_uploads")
        out_dir.mkdir(parents=True, exist_ok=True)

        for u in updates:
            msg = u.get("message") or u.get("channel_post") or {}
            update_id = u.get("update_id")
            caption = msg.get("caption", "")
            text = msg.get("text", "")
            photos = msg.get("photo", [])
            doc = msg.get("document", {})
            user = msg.get("from", {}).get("first_name", "User")
            chat_id = msg.get("chat", {}).get("id")

            print(f"[{update_id}] From: {user} ({chat_id}) | Text: '{text}' | Caption: '{caption}' | Photos: {len(photos)}")

            if photos:
                # Get largest photo
                best_photo = photos[-1]
                file_id = best_photo["file_id"]
                file_info_url = f"{TELEGRAM_API}/getFile?file_id={file_id}"
                with urllib.request.urlopen(file_info_url) as finfo_resp:
                    finfo = json.loads(finfo_resp.read().decode())
                    tg_path = finfo["result"]["file_path"]
                    ext = Path(tg_path).suffix or ".jpg"
                    dest_file = out_dir / f"tg_photo_{update_id}{ext}"
                    
                    dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_path}"
                    with urllib.request.urlopen(dl_url) as dl_r, open(dest_file, "wb") as out_f:
                        out_f.write(dl_r.read())
                    print(f"-> Successfully downloaded: {dest_file} ({dest_file.stat().st_size} bytes)")
                    saved_files.append(str(dest_file))

            elif doc:
                file_id = doc["file_id"]
                orig_name = doc.get("file_name", f"tg_doc_{update_id}")
                file_info_url = f"{TELEGRAM_API}/getFile?file_id={file_id}"
                with urllib.request.urlopen(file_info_url) as finfo_resp:
                    finfo = json.loads(finfo_resp.read().decode())
                    tg_path = finfo["result"]["file_path"]
                    dest_file = out_dir / orig_name
                    
                    dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{tg_path}"
                    with urllib.request.urlopen(dl_url) as dl_r, open(dest_file, "wb") as out_f:
                        out_f.write(dl_r.read())
                    print(f"-> Successfully downloaded doc: {dest_file} ({dest_file.stat().st_size} bytes)")
                    saved_files.append(str(dest_file))

        print(f"\nDONE! Downloaded {len(saved_files)} file(s).")

except Exception as e:
    print(f"Error checking updates: {e}")
