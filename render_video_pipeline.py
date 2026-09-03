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

# Media IDs from Option 1 and Option 2 (Refined)
MEDIA_ID_OPT1 = "e904f047-8511-4a48-b742-a9e9f46ee046" # Factory Conveyor
MEDIA_ID_OPT2 = "5c5995f9-76e6-4839-8d14-f97e3284fd4d" # Warehouse Pallet

out_dir = Path("outputs/nuoc_giat_paris_5l")
out_dir.mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("🚀 BẮT ĐẦU QUY TRÌNH RENDER VIDEO OMNI FLASH (24s - 30s)")
print("=" * 60)

scenes = [
    {
        "scene_id": 1,
        "title": "Cảnh 1: Hook giữ chân (Bối cảnh Xưởng đóng chai - Option 1)",
        "media_id": MEDIA_ID_OPT1,
        "duration": 8,
        "dialogue": "Chị em ơi, giặt đồ mùa này mà sợ ẩm mốc bốc mùi hôi thì chuyển ngay sang combo nước giặt xả Paris hương nước hoa Pháp này nha!",
        "prompt": (
            'Vertical 9:16 commercial video with native speech audio. The female presenter in reference image holding the Paris detergent bottle '
            'speaks directly and enthusiastically to the camera in natural Vietnamese: '
            '"Chị em ơi, giặt đồ mùa này mà sợ ẩm mốc bốc mùi hôi thì chuyển ngay sang combo nước giặt xả Paris hương nước hoa Pháp này nha!" '
            'Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, '
            'standing comfortably inside the modern factory workshop with subtle natural breathing and gentle hand gestures. '
            'Ultra-realistic commercial lighting, authentic human skin texture, shot on 35mm lens.'
        )
    },
    {
        "scene_id": 2,
        "title": "Cảnh 2: Tính năng & Công nghệ (Bối cảnh Kho hàng tổng - Option 2)",
        "media_id": MEDIA_ID_OPT2,
        "duration": 8,
        "dialogue": "Công nghệ giặt xả hai trong một siêu tiện lợi, đánh bay vết bẩn cứng đầu, kháng khuẩn vượt trội và lưu hương nước hoa thơm ngát gấp ba lần.",
        "prompt": (
            'Vertical 9:16 commercial video with native speech audio. The female presenter in reference image standing in the logistics warehouse holding the Paris detergent bottle '
            'speaks clearly and confidently to the camera in natural Vietnamese: '
            '"Công nghệ giặt xả hai trong một siêu tiện lợi, đánh bay vết bẩn cứng đầu, kháng khuẩn vượt trội và lưu hương nước hoa thơm ngát gấp ba lần." '
            'Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, '
            'gentle head nods, smiling warmly, holding the bottle securely at waist level. '
            'Authentic commercial photography lighting, ultra-realistic human skin details.'
        )
    },
    {
        "scene_id": 3,
        "title": "Cảnh 3: Kêu gọi hành động CTA (Bối cảnh Kho hàng tổng - Option 2)",
        "media_id": MEDIA_ID_OPT2,
        "duration": 8,
        "dialogue": "Combo tận mười lít dùng thả ga cho cả gia đình, mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi nha!",
        "prompt": (
            'Vertical 9:16 commercial video with native speech audio. The female presenter in reference image standing in the warehouse '
            'points her index finger towards the bottom left corner of the screen with an inviting, friendly smile and speaks in natural Vietnamese: '
            '"Combo tận mười lít dùng thả ga cho cả gia đình, mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi nha!" '
            'Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, '
            'dynamic engaging gesture pointing towards bottom-left corner of the frame, cheerful smile. '
            'Ultra-realistic commercial lighting, photorealistic 9:16 vertical video.'
        )
    }
]

# Step 1: Submit video generation tasks with retry mechanism
active_tasks = []

def submit_video_with_retry(fc, sc, max_retries=6, delay=15):
    for attempt in range(1, max_retries + 1):
        print(f"\n🎬 [Lần thử {attempt}/{max_retries}] Đang gửi lệnh render {sc['title']}...")
        op_name = fc.generate_video(
            prompt=sc["prompt"],
            reference_media_ids=[sc["media_id"]],
            duration_seconds=sc["duration"],
            aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT"
        )
        if op_name:
            print(f"✓ Khởi tạo thành công task: {op_name}")
            return op_name
        print(f"⚠️ Server Flow đang bận/đang nạp slot video (503). Chờ {delay}s trước khi thử lại...")
        time.sleep(delay)
    return None

for sc in scenes:
    op_name = submit_video_with_retry(fc, sc)
    if op_name:
        active_tasks.append({
            "scene_id": sc["scene_id"],
            "title": sc["title"],
            "op_name": op_name,
            "dialogue": sc["dialogue"]
        })
    else:
        print(f"❌ Không thể tạo video cho {sc['title']} sau các lần thử.")

if not active_tasks:
    print("❌ Không thể khởi tạo bất kỳ task render video nào!")
    sys.exit(1)

# Step 2: Poll status until all videos are completed
print("\n" + "=" * 60)
print(f"⏳ ĐANG THEO DÕI TIẾN ĐỘ RENDER CHO {len(active_tasks)} PHÂN CẢNH...")
print("=" * 60)

completed_videos = {}
op_names = [t["op_name"] for t in active_tasks]

start_poll_time = time.time()
max_poll_time = 480 # 8 minutes max

while time.time() - start_poll_time < max_poll_time:
    remaining_ops = [op for op in op_names if op not in completed_videos]
    if not remaining_ops:
        print("\n🎉 TẤT CẢ PHÂN CẢNH ĐÃ RENDER XONG!")
        break

    status_data = fc.get_video_status(remaining_ops)
    operations = status_data.get("operations") or status_data.get("data", {}).get("operations", [])
    if isinstance(status_data, list):
        operations = status_data

    for op_info in operations:
        name = op_info.get("name")
        done = op_info.get("done", False)
        status_str = op_info.get("status", "")
        
        if done or status_str in ["COMPLETED", "SUCCESS"]:
            # Extract video download URL
            response = op_info.get("response", {})
            video_url = None
            
            # Check various video URL fields
            if "videoUrl" in response:
                video_url = response["videoUrl"]
            elif "generatedVideos" in response:
                vids = response["generatedVideos"]
                if vids and len(vids) > 0:
                    video_url = vids[0].get("downloadUrl") or vids[0].get("fifeUrl")
            elif "videos" in response:
                vids = response["videos"]
                if vids and len(vids) > 0:
                    video_url = vids[0].get("downloadUrl") or vids[0].get("url")
            elif "downloadUrl" in response:
                video_url = response["downloadUrl"]
            elif "downloadUrl" in op_info:
                video_url = op_info["downloadUrl"]

            if video_url and name not in completed_videos:
                print(f"✓ Hoàn thành {name} -> URL: {video_url[:60]}...")
                completed_videos[name] = video_url

    print(f"[{int(time.time() - start_poll_time)}s] Tiến độ: {len(completed_videos)}/{len(op_names)} hoàn thành...")
    if len(completed_videos) < len(op_names):
        time.sleep(12)

# Step 3: Download scene videos
scene_files = []
for t in active_tasks:
    op_name = t["op_name"]
    sc_id = t["scene_id"]
    if op_name in completed_videos:
        url = completed_videos[op_name]
        dest_path = out_dir / f"scene_{sc_id}.mp4"
        print(f"\n📥 Đang tải Cảnh {sc_id} về {dest_path}...")
        if fc.download_file(url, str(dest_path)):
            scene_files.append(str(dest_path))
            print(f"✓ Đã lưu Cảnh {sc_id} ({dest_path.stat().st_size} bytes)")
        else:
            print(f"❌ Lỗi tải Cảnh {sc_id}")
    else:
        print(f"❌ Cảnh {sc_id} ({op_name}) chưa có video hoàn thành.")

# Step 4: Concatenate videos with FFmpeg
final_video_path = out_dir / "video_final.mp4"
root_final_video = Path("outputs") / "video_final_nuoc_giat_paris.mp4"

if len(scene_files) == len(scenes):
    print("\n🎬 Đang ghép nối 3 phân cảnh thành video hoàn chỉnh 24s bằng FFmpeg...")
    concat_list_file = out_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as cf:
        for sf in scene_files:
            abs_sf = os.path.abspath(sf).replace("\\", "/")
            cf.write(f"file '{abs_sf}'\n")

    cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c copy "{final_video_path}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if final_video_path.exists() and final_video_path.stat().st_size > 0:
        import shutil
        shutil.copyfile(final_video_path, root_final_video)
        print(f"✅ GHÉP VIDEO THÀNH CÔNG: {final_video_path} ({round(final_video_path.stat().st_size / (1024*1024), 2)} MB)")
    else:
        print(f"⚠️ Thử ghép nối re-encoding...")
        cmd2 = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_file}" -c:v libx264 -c:a aac "{final_video_path}"'
        subprocess.run(cmd2, shell=True)
        if final_video_path.exists():
            import shutil
            shutil.copyfile(final_video_path, root_final_video)
            print(f"✅ GHÉP VIDEO THÀNH CÔNG: {final_video_path}")
    
    if concat_list_file.exists():
        concat_list_file.unlink()

# Step 5: Send final video to Telegram
if final_video_path.exists() and final_video_path.stat().st_size > 0:
    print(f"\n📤 Đang gửi video hoàn thiện vào Telegram (@Genvideo1_bot)...")
    caption = (
        "🎬 <b>VIDEO QUẢNG CÁO TIKTOK SHOP HOÀN THIỆN (24s / 9:16)</b>\n\n"
        "📦 <b>Sản phẩm:</b> Combo 2 Can Nước Giặt Xả Paris Luxury Perfume 5in1 (10 Lít)\n"
        "✨ <b>Bối cảnh:</b> Chuyển cảnh từ Xưởng đóng chai hiện đại ➔ Kho hàng tổng pallet cao tầng\n"
        "🗣️ <b>Lồng thoại:</b> Tiếng Việt tự nhiên 100%, khẩu hình nhép môi chân thực\n"
        "🎯 <b>Cấu trúc:</b> Hook giải quyết ẩm mốc ➔ Công năng 2in1 lưu hương ➔ CTA giỏ hàng góc trái chuẩn chính sách."
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
print("🏁 HOÀN TẤT TOÀN BỘ QUY TRÌNH SẢN XUẤT VIDEO!")
print("=" * 60)
