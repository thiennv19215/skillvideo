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

MEDIA_ID_OPT2 = "5c5995f9-76e6-4839-8d14-f97e3284fd4d" # Warehouse Pallet

out_dir = Path("outputs/nuoc_giat_paris_5l")
out_dir.mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)

# 1. Download Scene 1 and Scene 3 which are already successfully rendered
url_scene1 = "https://flow-content.google/video/cd072bf8-3dbd-4b60-9b57-cbf812064142?Expires=1788384983&KeyName=labs-flow-prod-cdn-key&Signature=fcqAGZFAN8gFWR13OKg45s0HMSI"
url_scene3 = "https://flow-content.google/video/8da2b92e-691f-4cf0-a667-fbd9403e08a9?Expires=1788384999&KeyName=labs-flow-prod-cdn-key&Signature=U06LuPcCG12SifAR6md1UEe2i7A"

file_scene1 = out_dir / "scene_1.mp4"
file_scene3 = out_dir / "scene_3.mp4"
file_scene2 = out_dir / "scene_2.mp4"

print("📥 Đang tải Cảnh 1 (Hook - Xưởng sản xuất)...")
fc.download_file(url_scene1, str(file_scene1))
print(f"✓ Cảnh 1: {file_scene1.stat().st_size} bytes")

print("📥 Đang tải Cảnh 3 (CTA - Kho pallet)...")
fc.download_file(url_scene3, str(file_scene3))
print(f"✓ Cảnh 3: {file_scene3.stat().st_size} bytes")

# 2. Submit Scene 2
prompt_scene2 = (
    'Vertical 9:16 commercial video with native speech audio. The female presenter in reference image standing in the logistics warehouse holding the Paris detergent bottle '
    'speaks clearly and confidently to the camera in natural Vietnamese: '
    '"Công nghệ giặt xả hai trong một siêu tiện lợi, đánh bay vết bẩn cứng đầu, kháng khuẩn vượt trội và lưu hương nước hoa thơm ngát gấp ba lần." '
    'Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, '
    'gentle head nods, smiling warmly, holding the bottle securely at waist level. '
    'Authentic commercial photography lighting, ultra-realistic human skin details.'
)

print("\n🎬 Đang khởi tạo render Cảnh 2 (Tính năng 2in1)...")
op_scene2 = None
for attempt in range(1, 10):
    op_scene2 = fc.generate_video(
        prompt=prompt_scene2,
        reference_media_ids=[MEDIA_ID_OPT2],
        duration_seconds=8,
        aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT"
    )
    if op_scene2:
        print(f"✓ Đã khởi tạo thành công Cảnh 2: {op_scene2}")
        break
    print(f"⚠️ [Thử {attempt}/9] Slot video đang bận, chờ 10s rồi thử lại...")
    time.sleep(10)

if not op_scene2:
    print("❌ Không thể submit Cảnh 2")
    sys.exit(1)

# 3. Poll status for Scene 2
print(f"\n⏳ Đang theo dõi tiến độ Cảnh 2 ({op_scene2})...")
url_scene2 = None
start_t = time.time()

while time.time() - start_t < 360:
    res = fc.get_video_status([op_scene2])
    operations = res.get("operations") or res.get("data", {}).get("operations", [])
    if isinstance(res, list):
        operations = res
        
    for op in operations:
        status_obj = op.get("mediaMetadata", {}).get("mediaStatus", {})
        gen_status = status_obj.get("mediaGenerationStatus")
        dl_url = op.get("downloadUrl")
        
        if dl_url and (op.get("done") or gen_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL" or op.get("status") in ["COMPLETED", "SUCCESS"]):
            url_scene2 = dl_url
            print(f"🎉 CẢNH 2 ĐÃ HOÀN THÀNH: {url_scene2[:60]}...")
            break
            
    if url_scene2:
        break
        
    print(f"[{int(time.time() - start_t)}s] Cảnh 2 đang render...")
    time.sleep(10)

if not url_scene2:
    print("❌ Hết thời gian chờ Cảnh 2")
    sys.exit(1)

print("\n📥 Đang tải Cảnh 2 về máy...")
fc.download_file(url_scene2, str(file_scene2))
print(f"✓ Cảnh 2: {file_scene2.stat().st_size} bytes")

# 4. Concat all 3 scenes with FFmpeg
final_video_path = out_dir / "video_final.mp4"
root_final_video = Path("outputs") / "video_final_nuoc_giat_paris.mp4"

print("\n🎬 Đang ghép nối 3 phân cảnh thành video 24s bằng FFmpeg...")
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
    print(f"✅ GHÉP VIDEO THÀNH CÔNG: {final_video_path} ({round(final_video_path.stat().st_size / (1024*1024), 2)} MB)")

if concat_list_file.exists():
    concat_list_file.unlink()

# 5. Send to Telegram
if final_video_path.exists() and final_video_path.stat().st_size > 0:
    print(f"\n📤 Đang gửi video hoàn thiện vào Telegram (@Genvideo1_bot)...")
    caption = (
        "🎬 <b>VIDEO QUẢNG CÁO TIKTOK SHOP HOÀN THIỆN (24s / 9:16)</b>\n\n"
        "📦 <b>Sản phẩm:</b> Combo 2 Can Nước Giặt Xả Paris Luxury Perfume 5in1 (10 Lít)\n"
        "✨ <b>Bối cảnh kết hợp:</b> Xưởng đóng chai hiện đại ➔ Kho hàng tổng pallet cao tầng\n"
        "🗣️ <b>Lồng thoại tiếng Việt:</b> Chuẩn giọng tự nhiên, nhép môi khớp 100%\n"
        "🎯 <b>Cấu trúc 3 cảnh:</b>\n"
        "• <i>Cảnh 1 (8s):</i> Hook giải quyết nỗi đau ẩm mốc ngày mưa\n"
        "• <i>Cảnh 2 (8s):</i> Tính năng giặt xả 2in1 lưu hương nước hoa gấp 3 lần\n"
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
print("🏁 HOÀN TẤT TOÀN BỘ QUY TRÌNH!")
print("=" * 60)
