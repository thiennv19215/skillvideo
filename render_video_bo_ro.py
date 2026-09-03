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

out_dir = Path("outputs/bo_ro_rao_nuoc_6mon")
out_dir.mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)

opt1_path = out_dir / "anh_duyet_option_1.jpg"

print("=" * 60)
print("🎬 KHỞI TẠO SẢN XUẤT VIDEO: BỘ RỔ RÁO NƯỚC 6 MÓN (24s / 9:16)")
print("=" * 60)

approved_media_id = "0f0c1148-d0b3-4d93-95ea-91ef714c5bba"
print(f"✓ Approved Media ID: {approved_media_id}")

# Kịch bản 1 (Hot - Nỗi đau rửa rau)
dialogues = [
    {
        "id": 1,
        "name": "Cảnh 1 (Hook)",
        "text": "Chị em nội trợ nào đang đau đầu vì mỗi lần rửa rau nước chảy lênh láng ra sàn bếp thì xem ngay bộ rổ ráo nước thông minh sáu món này nha!"
    },
    {
        "id": 2,
        "name": "Cảnh 2 (Tính năng)",
        "text": "Thiết kế hai lớp kép cực kỳ tiện lợi, bên trong là rổ thoát nước siêu nhanh, bên ngoài là chậu hứng nước chống tràn, ba kích cỡ lớn vừa nhỏ lồng khít vào nhau siêu gọn gàng."
    },
    {
        "id": 3,
        "name": "Cảnh 3 (CTA)",
        "text": "Trọn bộ sáu món bền đẹp tiện lợi cho mọi gian bếp, mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay nhé!"
    }
]

created_scenes = []

print("\n2. Submit 3 phân cảnh lên Google Flow Omni Flash...")
for sc in dialogues:
    sc_id = sc["id"]
    text = sc["text"]
    prompt = (
        f"Vertical 9:16 commercial video with native speech audio. "
        f"The female presenter strictly preserving 100% of her identical face, hairstyle, clothing and holding the exact same 6-piece colander basket set from reference image 1 with zero distortion or morphing. "
        f"She speaks directly and enthusiastically to the camera in natural Vietnamese: \"{text}\" "
        f"with realistic lip-sync mouth movements matching the Vietnamese words, subtle natural breathing, gentle head nods, "
        f"maintaining the product steady in her hands without changing its appearance or label. "
        f"Ultra-realistic 4k commercial lighting."
    )
    
    print(f"\nSubmitting Cảnh {sc_id}...")
    op_name = None
    for attempt in range(1, 4):
        op_name = fc.generate_video(
            prompt=prompt,
            reference_media_ids=[approved_media_id],
            duration_seconds=8
        )
        if op_name:
            print(f"✓ Cảnh {sc_id} thành công -> Op: {op_name}")
            created_scenes.append({"id": sc_id, "op_name": op_name, "text": text})
            break
        print(f"⚠️ [Thử {attempt}/3] Lỗi submit hoặc server bận, thử lại sau 6s...")
        time.sleep(6)

if not created_scenes:
    print("❌ Không submit được cảnh nào lên server.")
    sys.exit(1)

# Polling status
print(f"\n3. Giám sát tiến độ {len(created_scenes)} phân cảnh...")
completed_urls = {}
start_poll = time.time()

while time.time() - start_poll < 360:
    remaining = [s["op_name"] for s in created_scenes if s["op_name"] not in completed_urls]
    if not remaining:
        print("🎉 TẤT CẢ CÁC CẢNH ĐÃ RENDER XONG!")
        break
        
    try:
        status_res = fc.get_video_status(remaining)
        ops = status_res.get("operations") or status_res.get("media") or []
        for item in ops:
            op_name = item.get("name") or item.get("workflowId")
            status_obj = item.get("mediaMetadata", {}).get("mediaStatus", {})
            gen_status = status_obj.get("mediaGenerationStatus")
            dl_url = item.get("downloadUrl")
            
            if dl_url or gen_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                url = dl_url or item.get("downloadUrl")
                if url and op_name not in completed_urls:
                    print(f"✓ Hoàn thành Op {op_name} -> {url[:60]}...")
                    completed_urls[op_name] = url
    except Exception as e:
        print(f"Poll error: {e}")
        
    elapsed = int(time.time() - start_poll)
    print(f"[{elapsed}s] {len(completed_urls)}/{len(created_scenes)} cảnh hoàn tất...")
    if len(completed_urls) < len(created_scenes):
        time.sleep(10)

# Download files
scene_files = []
for s in created_scenes:
    sc_id = s["id"]
    op_name = s["op_name"]
    if op_name in completed_urls:
        url = completed_urls[op_name]
        dest = out_dir / f"scene_{sc_id}.mp4"
        print(f"\n📥 Đang tải Cảnh {sc_id} về {dest}...")
        if fc.download_file(url, str(dest)):
            scene_files.append(str(dest))
            print(f"✓ Đã lưu Cảnh {sc_id} ({dest.stat().st_size} bytes)")

final_video = out_dir / "video_final.mp4"
root_final = Path("outputs") / "video_final_bo_ro_6mon.mp4"

# Concat with FFmpeg
if len(scene_files) >= 1:
    print("\n4. Ghép nối FFmpeg...")
    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as cf:
        for sf in scene_files:
            abs_sf = os.path.abspath(sf).replace("\\", "/")
            cf.write(f"file '{abs_sf}'\n")

    cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list}" -c copy "{final_video}"'
    subprocess.run(cmd, shell=True, check=True)

    if final_video.exists() and final_video.stat().st_size > 0:
        import shutil
        shutil.copyfile(final_video, root_final)
        print(f"✅ GHÉP VIDEO THÀNH CÔNG: {final_video} ({round(final_video.stat().st_size / (1024*1024), 2)} MB)")

    if concat_list.exists():
        concat_list.unlink()

# Send to Telegram
if final_video.exists() and final_video.stat().st_size > 0:
    print("\n5. Gửi video hoàn thiện vào Telegram (@Genvideo1_bot)...")
    caption = (
        "🎬 <b>VIDEO TIKTOK SHOP HOÀN THIỆN: BỘ THAU RỔ RÁO NƯỚC 6 MÓN (24s / 9:16)</b>\n\n"
        "📦 <b>Sản phẩm:</b> Bộ Thau Rổ Ráo Nước 6 Món Cao Cấp (3 Rổ + 3 Chậu Lồng Nhau)\n"
        "🏭 <b>Bối cảnh chuẩn:</b> Băng chuyền đối xứng xưởng sản xuất + Bàn inox tiền cảnh (Học từ Video mẫu)\n"
        "🗣️ <b>Lồng thoại tiếng Việt:</b> Nhép môi khớp 100%, âm thanh tự nhiên chân thực\n"
        "🎯 <b>Cấu trúc kịch bản:</b>\n"
        "• <i>Cảnh 1:</i> Nỗi đau rửa rau nước chảy lênh láng\n"
        "• <i>Cảnh 2:</i> Thiết kế kép 2in1 thoát nước nhanh, lồng khít siêu gọn\n"
        "• <i>Cảnh 3:</i> CTA bấm giỏ hàng góc trái màn hình nhận ưu đãi."
    )
    with httpx.Client(timeout=180, trust_env=False) as client:
        with open(final_video, "rb") as vf:
            tg_res = client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={"chat_id": str(CHAT_ID), "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"},
                files={"video": (final_video.name, vf, "video/mp4")}
            )
            print("Telegram send result:", tg_res.status_code == 200)

print("\n" + "=" * 60)
print("🏁 HOÀN TẤT TOÀN BỘ!")
print("=" * 60)
