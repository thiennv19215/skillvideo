import sys
import os
import json
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from services.flow_client import FlowClient

fc = FlowClient()

char_path = "models/images/character_portrait.png"
prod_path = "inputs/products/nuoc_giat_paris_5l/product_image_1.jpg"
out_dir = Path("outputs/nuoc_giat_paris_5l")
out_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("🚀 SINH LẠI 3 OPTION ẢNH DUYỆT (GÓC RỘNG TỰ NHIÊN & DA THỰC KHÔNG BỘT)")
print("=" * 60)

# 1. Upload images
char_res = fc.upload_image(char_path)
char_media_id = char_res.get("name") if char_res else None

prod_res = fc.upload_image(prod_path)
prod_media_id = prod_res.get("name") if prod_res else None

if not char_media_id or not prod_media_id:
    print("❌ Lỗi upload ảnh!")
    sys.exit(1)

print(f"✓ Char ID: {char_media_id} | Prod ID: {prod_media_id}")

# Improved Prompt Components:
# 1. Medium shot, not too close-up, spacious background framing
FRAMING_PROMPT = (
    "Medium three-quarter shot, natural camera distance of 2.5 meters, comfortable headroom and wide spacious framing, "
    "not a tight close-up, showing her upper body down to hips and deep background environment with realistic depth of field. "
)

# 2. Strict character identity
CHAR_PROMPT = (
    "The exact same 26-year-old Asian woman from reference image 1, strictly preserving 100% of her identical face, "
    "identical facial structure, identical natural double-eyelid eye shape, identical gentle warm smile, and identical high bun hairstyle with thin parted side strands. "
)

# 3. Raw authentic skin realism (NO powdery/airbrushed/plastic skin)
RAW_SKIN_PROMPT = (
    "Raw authentic real-life commercial photograph, 100% natural human skin texture with visible micro pores, fine natural skin grain, "
    "natural subsurface scattering, authentic skin tones, zero powder effect, absolutely no airbrushed smooth plastic skin, no CGI, "
    "no 3D render, no anime, no beauty filter, shot on 50mm f/2.8 professional camera lens, ultra crisp sharp focus. 9:16 vertical ratio."
)

options = [
    {
        "id": 1,
        "name": "Option 1 - Xưởng sản xuất hiện đại (Góc rộng sâu)",
        "filename": "anh_duyet_option_1.jpg",
        "prompt": (
            f"{FRAMING_PROMPT}{CHAR_PROMPT}"
            f"She is standing comfortably on the bright floor of a modern liquid detergent factory workshop, with an automated packaging conveyor line and steel tanks clearly visible with depth in the background. "
            f"She is holding the 5L black Paris Luxury Perfume detergent bottle from reference image 2 with both hands at waist level, accurate realistic 5L gallon scale to human body (~32cm height, not oversized). "
            f"{RAW_SKIN_PROMPT}"
        )
    },
    {
        "id": 2,
        "name": "Option 2 - Kệ pallet kho hàng cao tầng (Góc rộng sâu)",
        "filename": "anh_duyet_option_2.jpg",
        "prompt": (
            f"{FRAMING_PROMPT}{CHAR_PROMPT}"
            f"She is standing in a spacious high-bay logistics warehouse aisle, with tall industrial storage racks holding stacked Paris detergent cartons stretching into the background with realistic perspective. "
            f"She is holding the 5L black Paris Luxury Perfume detergent bottle from reference image 2 with both hands in front of her, accurate realistic handheld 5L gallon proportions. "
            f"{RAW_SKIN_PROMPT}"
        )
    },
    {
        "id": 3,
        "name": "Option 3 - Phòng giặt gia đình ấm cúng (Góc rộng tự nhiên)",
        "filename": "anh_duyet_option_3.jpg",
        "prompt": (
            f"{FRAMING_PROMPT}{CHAR_PROMPT}"
            f"She is standing in a spacious, sunlit modern home laundry room, standing next to a front-load washing machine and counter with folded cotton towels and natural sunlight streaming from a side window. "
            f"She is holding the 5L purple Paris Luxury Perfume detergent bottle from reference image 2 with both hands, accurate realistic 5L proportions. "
            f"{RAW_SKIN_PROMPT}"
        )
    }
]

results = []

for opt in options:
    print(f"\n🎨 Đang tạo {opt['name']}...")
    try:
        media_list = fc.generate_image(
            prompt=opt["prompt"],
            reference_media_ids=[char_media_id, prod_media_id],
            aspect_ratio="IMAGE_ASPECT_RATIO_PORTRAIT",
            model="NANO_BANANA_PRO",
            variant_count=1
        )
        
        if media_list and len(media_list) > 0:
            item = media_list[0]
            dl_url = item.get("downloadUrl") or item.get("image", {}).get("generatedImage", {}).get("fifeUrl")
            img_media_id = item.get("name")
            
            if dl_url:
                target_path = out_dir / opt["filename"]
                fc.download_file(dl_url, str(target_path))
                root_out_path = Path("outputs") / opt["filename"]
                fc.download_file(dl_url, str(root_out_path))
                
                print(f"✓ Đã lưu: {target_path} (Media ID: {img_media_id})")
                results.append({
                    "option_id": opt["id"],
                    "name": opt["name"],
                    "media_id": img_media_id,
                    "download_url": dl_url,
                    "local_path": str(target_path).replace("\\", "/"),
                    "root_path": str(root_out_path).replace("\\", "/")
                })
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# Save updated metadata
with open(out_dir / "options_metadata.json", "w", encoding="utf-8") as f:
    json.dump({
        "product_id": "nuoc_giat_paris_5l",
        "char_media_id": char_media_id,
        "prod_media_id": prod_media_id,
        "options": results,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print(f"✅ ĐÃ SINH LẠI XONG {len(results)}/3 ẢNH DUYỆT!")
print("=" * 60)
