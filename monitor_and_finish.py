import sys
import os
import json
import time
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
from services.flow_client import FlowClient

fc = FlowClient()

CONFIG_PATH = Path("config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config.get("telegram", {}).get("bot_token")
CHAT_ID = 883815873

WORKFLOW_ID_SCENE2 = "62cf238e-2639-48ce-8c7f-b59b61ec0cdf"
out_dir = Path("outputs/nuoc_giat_paris_5l")
out_dir.mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)

file_scene1 = out_dir / "scene_1.mp4"
file_scene2 = out_dir / "scene_2.mp4"
file_scene3 = out_dir / "scene_3.mp4"
final_video_path = out_dir / "video_final.mp4"
root_final_video = Path("outputs") / "video_final_nuoc_giat_paris.mp4"

print(f"⏳ Đang theo dõi trực tiếp Cảnh 2 (Workflow: {WORKFLOW_ID_SCENE2})...")
start_time = time.time()
dl_url_scene2 = None

while time.time() - start_time < 300:
    try:
        with httpx.Client(timeout=30, trust_env=False) as client:
            res = client.post(f"{fc.base_url}/v1/videos/status", json={"operation_names": [WORKFLOW_ID_SCENE2]})
            if res.status_code == 200:
                data = res.json()
                media_list = data.get("media") or data.get("operations") or []
                for item in media_list:
                    status_obj = item.get("mediaMetadata", {}).get("mediaStatus", {})
                    gen_status = status_obj.get("mediaGenerationStatus")
                    url = item.get("downloadUrl")
                    
                    if not url and "video" in item:
                        # Check operation inside video
                        pass

                    if url or gen_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                        dl_url_scene2 = url or item.get("downloadUrl")
                        print(f"\n🎉 CẢNH 2 ĐÃ RENDER XONG! URL: {dl_url_scene2[:60]}...")
                        break
    except Exception as e:
        print(f"Lỗi kiểm tra status: {e}")

    if dl_url_scene2:
        break

    elapsed = int(time.time() - start_time)
    print(f"[{elapsed}s] Cảnh 2 đang xử lý (Omni Flash)...")
    time.sleep(10)

if not dl_url_scene2:
    print("❌ Hết thời gian chờ render Cảnh 2.")
    sys.exit(1)

# Download Scene 2
print("\n📥 Đang tải Cảnh 2 về outputs/nuoc_giat_paris_5l/scene_2.mp4...")
fc.download_file(dl_url_scene2, str(file_scene2))
print(f"✓ Cảnh 2 tải thành công: {file_scene2.stat().st_size} bytes")

# Concat with FFmpeg
print("\n🎬 Đang ghép nối 3 phân cảnh (Cảnh 1 + Cảnh 2 + Cảnh 3) thành video hoàn chỉnh 24s...")
concat_list_file = out_dir / "concat_list.txt"
with open(concat_list_file, "w", encoding="utf-8") as cf:
    for sf in [file_scene1, file_scene2, file_scene3]:
        abs_sf = os.path.abspath(sf).replace("\\", "/")
        cf.write(f"file '{abs_sf}'\n")

cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c copy "{final_video_path}"'
subprocess.run(cmd, shell=True, check=True)

if final_video_path.exists() and final_video_path.stat().st_size > 0:
    import shutil
    shutil.copyfile(final_video_path, root_final_video)
    print(f"✅ GHÉP VIDEO HOÀN TẤT: {final_video_path} ({round(final_video_path.stat().st_size / (1024*1024), 2)} MB)")

if concat_list_file.exists():
    concat_list_file.unlink()

# Send to Telegram
if final_video_path.exists() and final_video_path.stat().st_size > 0:
    print(f"\n📤 Đang gửi video hoàn thiện vào Telegram (@Genvideo1_bot)...")
    caption = (
        "🎬 <b>VIDEO QUẢNG CÁO TIKTOK SHOP HOÀN THIỆN (24s / 9:16)</b>\n\n"
        "📦 <b>Sản phẩm:</b> Combo 2 Can Nước Giặt Xả Paris Luxury Perfume 5in1 (10 Lít)\n"
        "✨ <b>Bối cảnh kết hợp:</b> Xưởng đóng chai hiện đại ➔ Kho hàng tổng pallet cao tầng\n"
        "🗣️ <b>Lồng thoại tiếng Việt:</b> 100% tự nhiên, nhép môi chân thực\n"
        "🎯 <b>Cấu trúc 3 phân cảnh:</b>\n"
        "• <i>Cảnh 1 (8s):</i> Hook giải quyết nỗi đau ẩm mốc ngày mưa\n"
        "• <i>Cảnh 2 (8s):</i> Công nghệ giặt xả 2in1 lưu hương nước hoa gấp 3 lần\n"
        "• <i>Cảnh 3 (8s):</i> CTA bấm giỏ hàng góc trái nhận ưu đãi."
    )
    with httpx.Client(timeout=180, trust_env=False) as client:
        with open(final_video_path, "rb") as vf:
            tg_res = client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={"chat_id": str(CHAT_ID), "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"},
                files={"video": (final_video_path.name, vf, "video/mp4")}
            )
            print("Telegram send video result:", tg_res.status_code == 200)

print("\n" + "=" * 60)
print("🏁 HOÀN TẤT TOÀN BỘ!")
print("=" * 60)
