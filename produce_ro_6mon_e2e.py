import sys
import os
import json
import time
import random
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

char_path = "models/images/character_portrait.png"
prod_path = "inputs/products/bo_ro_rao_nuoc_6mon/product_image_1.jpg"
out_dir = Path("outputs/bo_ro_rao_nuoc_6mon")
out_dir.mkdir(parents=True, exist_ok=True)
Path("outputs").mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("🚀 BẮT ĐẦU QUY TRÌNH E2E SẢN XUẤT VIDEO: BỘ RỔ RÁO NƯỚC 6 MÓN")
print("=" * 65)

# -------------------------------------------------------------
# BƯỚC 1: MEDIA IDS ĐÃ SẴN SÀNG TRÊN FLOW SERVER
# -------------------------------------------------------------
char_media_id = "b66f5ea9-abf3-4aae-a87f-11375d715ae5"
prod_media_id = "3c79f756-a58b-4e20-8d0f-5781028b6b8f"

print(f"✓ Nhân vật Media ID: {char_media_id}")
print(f"✓ Sản phẩm Media ID: {prod_media_id}")

# -------------------------------------------------------------
# BƯỚC 2: SOẠN 2 KỊCH BẢN HOT NHẤT & CHỌN RANDOM
# -------------------------------------------------------------
script_options = [
    {
        "id": "script_1_pain_point_focus",
        "title": "Kịch bản 1 (Hot): Nỗi đau rửa rau chảy nước lênh láng & Giải pháp ráo nước thông minh",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Cảnh 1 (Hook giữ chân - 8s)",
                "dialogue": "Chị em nội trợ nào đang đau đầu vì mỗi lần rửa rau nước chảy lênh láng ra sàn bếp thì xem ngay bộ rổ ráo nước thông minh sáu món này nha!",
                "bg_type": "factory_hall"
            },
            {
                "scene_id": 2,
                "title": "Cảnh 2 (Tính năng vượt trội - 8s)",
                "dialogue": "Thiết kế hai lớp kép cực kỳ tiện lợi, bên trong là rổ thoát nước siêu nhanh, bên ngoài là chậu hứng nước chống tràn, ba kích cỡ lớn vừa nhỏ lồng khít vào nhau siêu gọn gàng.",
                "bg_type": "factory_hall"
            },
            {
                "scene_id": 3,
                "title": "Cảnh 3 (CTA Kêu gọi mua - 8s)",
                "dialogue": "Trọn bộ sáu món bền đẹp tiện lợi cho mọi gian bếp, mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay nhé!",
                "bg_type": "factory_hall"
            }
        ]
    },
    {
        "id": "script_2_smart_kitchen_solution",
        "title": "Kịch bản 2 (Hot): Giải pháp gian bếp hiện đại & Trải nghiệm tận xưởng sản xuất",
        "scenes": [
            {
                "scene_id": 1,
                "title": "Cảnh 1 (Hook giữ chân - 8s)",
                "dialogue": "Một giải pháp cứu tinh cho gian bếp đây rồi cả nhà ơi! Rửa rau củ quả vừa sạch vừa ráo nước tinh tươm với bộ thau rổ sáu món tiện ích này nè!",
                "bg_type": "factory_hall"
            },
            {
                "scene_id": 2,
                "title": "Cảnh 2 (Tính năng vượt trội - 8s)",
                "dialogue": "Nhựa nguyên sinh dày dặn cao cấp, phối màu xanh vàng hiện đại, có quai xách hai bên và miệng rót nước thông minh, dùng xong xếp lồng lại tiết kiệm diện tích tối đa.",
                "bg_type": "factory_hall"
            },
            {
                "scene_id": 3,
                "title": "Cảnh 3 (CTA Kêu gọi mua - 8s)",
                "dialogue": "Bộ sáu món siêu tiện ích chuẩn xưởng cho cả gia đình, các bác nhanh tay bấm ngay vào giỏ hàng góc trái màn hình để sở hữu ngay nha!",
                "bg_type": "factory_hall"
            }
        ]
    }
]

selected_script = random.choice(script_options)
print(f"\n🎯 ĐÃ CHỌN RANDOM KỊCH BẢN HOT PHÙ HỢP NHẤT: {selected_script['title']}")

# -------------------------------------------------------------
# BƯỚC 3: TẠO ẢNH MẪU DUYỆT (HỌC TỪ VIDEO MẪU: BĂNG CHUYỀN ĐỐI XỨNG + BÀN INOX)
# -------------------------------------------------------------
print("\n[Bước 3/5] Tạo ảnh mẫu chuẩn học phong cách từ Video Mẫu (Băng chuyền xưởng đối xứng + Bàn inox tiền cảnh)...")

prompt_image_opt1 = (
    "Inside a massive clean modern manufacturing factory hall, standing centered between two long symmetrical production assembly conveyor lines stretching far back into the distance, "
    "with uniformed workers assembling products on both sides, industrial LED overhead lighting, polished clean epoxy floor. "
    "In the foreground on a gleaming reflective stainless steel workbench, multiple neat nesting sets of the dark teal and yellow 6-piece colander basket set and fresh vegetables are arranged orderly. "
    "The exact same 26-year-old Asian woman from reference image 1, strictly preserving 100% of her identical face, identical double eyelid eyes, identical nose, identical warm friendly smile, "
    "and identical hairstyle tied in a bun with parted side fringe strands. She is wearing a neat clean polo shirt, standing comfortably at a 2.5 meter medium three-quarter camera distance. "
    "She is holding the exact nesting 6-piece dark teal and yellow colander basket set from reference image 2 with both hands at waist height, accurate realistic handheld product dimensions (~26cm width). "
    "Raw authentic real-life commercial photography, realistic natural human skin texture with subtle micro pores, authentic optical depth of field, real factory ambient lighting, shot on 50mm DSLR lens, photorealistic, no 3D render, no CGI, no anime, no plastic airbrushed skin. Vertical 9:16 portrait."
)

prompt_image_opt2 = (
    "Inside a spacious modern distribution logistics warehouse, centered in an open aisle with massive multi-tier high-bay pallet storage racks stretching into the background with realistic depth. "
    "The exact same 26-year-old Asian woman from reference image 1, strictly preserving 100% of her identical face, identical facial features, identical hairstyle (high bun with parted side hair strands), "
    "identical warm smile, and identical skin tone with absolutely zero modifications. She is holding the exact nesting 6-piece dark teal and yellow colander basket set from reference image 2 in front of her with both hands, "
    "accurate realistic product proportions, perfectly scaled to human body, natural realistic size. "
    "Raw authentic real-life commercial photograph, 100% natural human skin texture with visible micro pores, authentic skin tones, zero powder effect, absolutely no airbrushed smooth plastic skin, no CGI, "
    "shot on 50mm lens, ultra crisp sharp focus. Vertical 9:16 ratio."
)

img_options = [
    {"id": 1, "name": "Option 1 (Xưởng đối xứng + Bàn inox tiền cảnh)", "prompt": prompt_image_opt1, "file": "anh_duyet_option_1.jpg"},
    {"id": 2, "name": "Option 2 (Kệ kho pallet cao tầng)", "prompt": prompt_image_opt2, "file": "anh_duyet_option_2.jpg"}
]

approved_media_ids = {}

for img_opt in img_options:
    print(f"🎨 Đang tạo {img_opt['name']}...")
    try:
        media_list = fc.generate_image(
            prompt=img_opt["prompt"],
            reference_media_ids=[char_media_id, prod_media_id],
            aspect_ratio="IMAGE_ASPECT_RATIO_PORTRAIT",
            model="NANO_BANANA_PRO",
            variant_count=1
        )
        if media_list and len(media_list) > 0:
            item = media_list[0]
            dl_url = item.get("downloadUrl") or item.get("image", {}).get("generatedImage", {}).get("fifeUrl")
            mid = item.get("name")
            if dl_url:
                target_f = out_dir / img_opt["file"]
                fc.download_file(dl_url, str(target_f))
                approved_media_ids[img_opt["id"]] = mid
                print(f"✓ Đã lưu {img_opt['name']}: {target_f} (Media ID: {mid})")
    except Exception as e:
        print(f"❌ Lỗi tạo {img_opt['name']}: {e}")

# Use Option 1 (Xưởng đối xứng phong cách video mẫu 1) as primary reference for video
primary_video_media_id = approved_media_ids.get(1) or approved_media_ids.get(2)
if not primary_video_media_id:
    print("❌ Không có ảnh mẫu nào được tạo thành công!")
    sys.exit(1)

print(f"\n✓ Sử dụng Media ID ảnh duyệt: {primary_video_media_id} để render Video!")

# -------------------------------------------------------------
# BƯỚC 4: RENDER 3 PHÂN CẢNH VIDEO (OMNI FLASH - BẢO TOÀN THAM CHIẾU)
# -------------------------------------------------------------
print("\n[Bước 4/5] Đang khởi tạo render 3 phân cảnh video Omni Flash...")

scene_tasks = []

for sc in selected_script["scenes"]:
    sc_id = sc["scene_id"]
    dialogue = sc["dialogue"]
    
    video_prompt = (
        f"Vertical 9:16 commercial video with native speech audio. "
        f"The female presenter strictly preserving 100% of her identical face, hairstyle, clothing and holding the exact same product from reference image 1 with zero distortion or morphing. "
        f"She speaks directly and enthusiastically to the camera in natural Vietnamese: \"{dialogue}\" "
        f"with realistic lip-sync mouth movements matching the Vietnamese words, subtle natural breathing, gentle head nods, "
        f"maintaining the product steady in her hands without changing its appearance or label. "
        f"Ultra-realistic 4k commercial lighting."
    )
    
    print(f"\n🎬 Đang submit Cảnh {sc_id}...")
    op_name = None
    for attempt in range(1, 8):
        op_name = fc.generate_video(
            prompt=video_prompt,
            reference_media_ids=[primary_video_media_id],
            duration_seconds=8,
            aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT"
        )
        if op_name:
            print(f"✓ Cảnh {sc_id} khởi tạo thành công: {op_name}")
            scene_tasks.append({
                "scene_id": sc_id,
                "title": sc["title"],
                "dialogue": dialogue,
                "op_name": op_name
            })
            break
        print(f"⚠️ [Thử {attempt}/7] Server đang bận slot, chờ 12s...")
        time.sleep(12)

if len(scene_tasks) < 3:
    print(f"⚠️ Chỉ khởi tạo được {len(scene_tasks)}/3 cảnh. Tiến hành theo dõi các cảnh đã tạo...")

# Poll video status
completed_scene_urls = {}
start_poll = time.time()
poll_timeout = 500

print("\n⏳ Đang theo dõi tiến độ render thời gian thực...")
while time.time() - start_poll < poll_timeout:
    remaining_ops = [t["op_name"] for t in scene_tasks if t["op_name"] not in completed_scene_urls]
    if not remaining_ops:
        print("\n🎉 TẤT CẢ PHÂN CẢNH ĐÃ RENDER XONG!")
        break
        
    try:
        status_res = fc.get_video_status(remaining_ops)
        operations = status_res.get("operations") or status_res.get("data", {}).get("operations") or status_res.get("media") or []
        if isinstance(status_res, list):
            operations = status_res
            
        for op in operations:
            op_name = op.get("name") or op.get("workflowId")
            status_obj = op.get("mediaMetadata", {}).get("mediaStatus", {})
            gen_status = status_obj.get("mediaGenerationStatus")
            dl_url = op.get("downloadUrl")
            
            if dl_url or gen_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL" or op.get("done") or op.get("status") in ["COMPLETED", "SUCCESS"]:
                url = dl_url or op.get("downloadUrl")
                if url and op_name not in completed_scene_urls:
                    print(f"✓ Hoàn thành {op_name} -> {url[:60]}...")
                    completed_scene_urls[op_name] = url
    except Exception as e:
        print(f"Polling error: {e}")
        
    elapsed = int(time.time() - start_poll)
    print(f"[{elapsed}s] Tiến độ: {len(completed_scene_urls)}/{len(scene_tasks)} cảnh hoàn thành...")
    if len(completed_scene_urls) < len(scene_tasks):
        time.sleep(10)

# Download scene files
scene_files = []
for t in scene_tasks:
    op_name = t["op_name"]
    sc_id = t["scene_id"]
    if op_name in completed_scene_urls:
        url = completed_scene_urls[op_name]
        dest = out_dir / f"scene_{sc_id}.mp4"
        print(f"\n📥 Đang tải Cảnh {sc_id} về {dest}...")
        if fc.download_file(url, str(dest)):
            scene_files.append(str(dest))
            print(f"✓ Đã lưu Cảnh {sc_id} ({dest.stat().st_size} bytes)")

# -------------------------------------------------------------
# BƯỚC 5: GHÉP NỐI FFMPEG VÀ GỬI TELEGRAM
# -------------------------------------------------------------
final_video_path = out_dir / "video_final.mp4"
root_final_video = Path("outputs") / "video_final_bo_ro_6mon.mp4"

if len(scene_files) >= 2:
    print("\n[Bước 5/5] Ghép nối các phân cảnh thành video hoàn chỉnh bằng FFmpeg...")
    concat_list = out_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as cf:
        for sf in scene_files:
            abs_sf = os.path.abspath(sf).replace("\\", "/")
            cf.write(f"file '{abs_sf}'\n")

    cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list}" -c copy "{final_video_path}"'
    subprocess.run(cmd, shell=True, check=True)

    if final_video_path.exists() and final_video_path.stat().st_size > 0:
        import shutil
        shutil.copyfile(final_video_path, root_final_video)
        print(f"✅ GHÉP VIDEO HOÀN TẤT: {final_video_path} ({round(final_video_path.stat().st_size / (1024*1024), 2)} MB)")

    if concat_list.exists():
        concat_list.unlink()

# Send to Telegram
if final_video_path.exists() and final_video_path.stat().st_size > 0:
    print(f"\n📤 Đang gửi video hoàn thiện vào Telegram (@Genvideo1_bot)...")
    caption = (
        "🎬 <b>VIDEO QUẢNG CÁO TIKTOK SHOP HOÀN THIỆN (24s / 9:16)</b>\n\n"
        "📦 <b>Sản phẩm:</b> Bộ Thau Rổ Kép Ráo Nước 6 Món Cao Cấp (3 Rổ + 3 Chậu)\n"
        f"🎯 <b>Kịch bản áp dụng:</b> {selected_script['title']}\n"
        "🏭 <b>Phong cách bối cảnh:</b> Học từ Video mẫu - Dây chuyền băng chuyền xưởng đối xứng + Bàn inox tiền cảnh\n"
        "🗣️ <b>Lồng thoại tiếng Việt:</b> Nhép môi khớp 100%, phong thái tự nhiên chân thực\n"
        "✨ <b>Bảo toàn tham chiếu:</b> Nhân vật và sản phẩm đồng nhất 100% không biến dạng."
    )
    with httpx.Client(timeout=180, trust_env=False) as client:
        with open(final_video_path, "rb") as vf:
            tg_res = client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={"chat_id": str(CHAT_ID), "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"},
                files={"video": (final_video_path.name, vf, "video/mp4")}
            )
            print("Telegram send video result:", tg_res.status_code == 200)

print("\n" + "=" * 65)
print("🏁 HOÀN TẤT TOÀN BỘ QUY TRÌNH E2E SẢN XUẤT VIDEO!")
print("=" * 65)
