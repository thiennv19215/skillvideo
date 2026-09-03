import os
import sys
import json
import time
import logging
import subprocess
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

LEARNED_TEMPLATES_FILE = "prompts/learned_templates.json"
HOOKS_LIBRARY_FILE = "prompts/hooks_library.json"

class SampleVideoAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini AI Client for Video Analysis & Learning.")
            except Exception as e:
                logger.warning(f"Could not init Gemini: {e}")

    def load_learned_templates(self) -> List[Dict[str, Any]]:
        if os.path.exists(LEARNED_TEMPLATES_FILE):
            try:
                with open(LEARNED_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("templates", [])
            except Exception as e:
                logger.error(f"Error loading learned templates: {e}")
        return []

    def save_learned_template(self, template_data: Dict[str, Any]):
        os.makedirs(os.path.dirname(LEARNED_TEMPLATES_FILE), exist_ok=True)
        templates = self.load_learned_templates()
        src_video = template_data.get("source_video")
        
        # Deduplicate by source_video or id
        existing_idx = next((i for i, t in enumerate(templates) if t.get("source_video") == src_video or t.get("id") == template_data.get("id")), None)
        if existing_idx is not None:
            templates[existing_idx] = template_data
        else:
            templates.append(template_data)

        with open(LEARNED_TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump({"templates": templates, "updated_at": time.time()}, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved learned template '{template_data.get('name')}' to {LEARNED_TEMPLATES_FILE}")

    def extract_keyframes(self, video_path: str, output_dir: str, count: int = 3) -> List[str]:
        """Extracts representative keyframe images from the video"""
        os.makedirs(output_dir, exist_ok=True)
        keyframe_paths = []
        try:
            # Extract frames at 1s, 4s, 7s
            timestamps = [1.0, 4.0, 7.0]
            for i, ts in enumerate(timestamps[:count]):
                out_img = os.path.join(output_dir, f"frame_{i+1}.jpg")
                cmd = f'ffmpeg -y -ss {ts} -i "{video_path}" -vframes 1 -q:v 2 "{out_img}"'
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(out_img):
                    keyframe_paths.append(out_img)
        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
        return keyframe_paths

    def analyze_and_learn_from_video(self, video_path: str, caption_hint: str = "") -> Dict[str, Any]:
        """Analyzes sample video structure, visual context, pacing, hook formula, and saves as reusable template"""
        file_name = os.path.basename(video_path)
        clean_name = os.path.splitext(file_name)[0]
        template_id = f"tpl_learned_{clean_name}_{int(time.time())}"

        frames_dir = os.path.join("outputs", "learned_frames", clean_name)
        keyframes = self.extract_keyframes(video_path, frames_dir, count=3)

        # AI Analysis if client available
        learned_info = None
        if self.client and keyframes:
            try:
                from PIL import Image
                pil_imgs = [Image.open(kf) for kf in keyframes if os.path.exists(kf)]

                prompt = (
                    "Bạn là chuyên gia phân tích video TikTok Shop viral.\n"
                    "Hãy nhìn vào các khung hình trích xuất từ video mẫu này và phân tích sâu cấu trúc kịch bản, bối cảnh, và yếu tố thu hút để tạo ra một TEMPLATE TÁI SỬ DỤNG ĐƯỢC CHO NHIỀU SẢN PHẨM KHÁC NHAU.\n\n"
                    "YÊU CẦU TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON:\n"
                    "{\n"
                    '  "name": "Tên phong cách ngắn gọn (VD: Xả Kho Dồn Dập / Review Bếp Thực Chiến / Đập Hộp Trải Nghiệm)",\n'
                    '  "hook_concept": "Ý tưởng hook mở đầu 3s thu hút (VD: Bác nào bị đau lưng... / Đang đứng tại xưởng...)",\n'
                    '  "hook_template": "Công thức câu mở đầu có biến {product_name} và {benefit}",\n'
                    '  "environment_desc": "Mô tả chi tiết bối cảnh thị giác (Ánh sáng, hậu cảnh kho/xưởng/nhà bếp/phòng ngủ)",\n'
                    '  "outfit_desc": "Trang phục nhân vật (Áo thun, sơ mi, tạp dề, smart-casual...)",\n'
                    '  "pacing": "Nhịp điệu nói (Dồn dập nhanh 28 từ/8s, hoặc ấm áp chia sẻ 22 từ/8s)",\n'
                    '  "cta_style": "Cách kêu gọi mua hàng giỏ hàng góc trái",\n'
                    '  "key_success_factors": ["Điểm thu hút 1", "Điểm thu hút 2"]\n'
                    "}"
                )

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[*pil_imgs, prompt, f"Ghi chú kèm theo: {caption_hint}"]
                )
                
                raw_text = response.text
                match = re.search(r"\{[\s\S]*\}", raw_text)
                if match:
                    learned_info = json.loads(match.group(0))
            except Exception as e:
                logger.warning(f"AI video learning analysis failed: {e}")

        if not learned_info:
            # Smart default template learning
            learned_info = {
                "name": f"Phong cách học từ {clean_name}",
                "hook_concept": "Săn deal trực tiếp theo nhịp video mẫu",
                "hook_template": "Bác nào đang tìm kiếm giải pháp tiện ích {benefit} thì bơi hết vào đây xem em khui chiếc {product_name} này nha!",
                "environment_desc": "Bối cảnh chuyên nghiệp, ánh sáng thương mại sắc nét, góc quay trung cảnh tự nhiên",
                "outfit_desc": "Trang phục hiện đại năng động, gương mặt thân thiện",
                "pacing": "Nhịp điệu dồn dập, tự nhiên, chuẩn TikTok Shop 24-28 từ/8s",
                "cta_style": "Bấm ngay vào giỏ hàng góc trái màn hình để nhận trọn vẹn ưu đãi",
                "key_success_factors": ["Bám sát nhịp điệu video mẫu", "Cận cảnh công năng sản phẩm"]
            }

        template_data = {
            "id": template_id,
            "source_video": file_name,
            "created_at": time.time(),
            "date_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            **learned_info
        }

        self.save_learned_template(template_data)

        # Also register hook into hooks_library.json if valid
        if "hook_template" in template_data:
            self._update_hooks_library(template_data)

        return template_data

    def _update_hooks_library(self, template_data: Dict[str, Any]):
        try:
            os.makedirs(os.path.dirname(HOOKS_LIBRARY_FILE), exist_ok=True)
            hooks_data = {"hooks": []}
            if os.path.exists(HOOKS_LIBRARY_FILE):
                with open(HOOKS_LIBRARY_FILE, "r", encoding="utf-8") as f:
                    hooks_data = json.load(f)
            
            hooks_list = hooks_data.get("hooks", [])
            new_hook = {
                "id": template_data.get("id"),
                "style": template_data.get("name"),
                "text": template_data.get("hook_template"),
                "learned_from": template_data.get("source_video")
            }
            hooks_list.append(new_hook)
            hooks_data["hooks"] = hooks_list

            with open(HOOKS_LIBRARY_FILE, "w", encoding="utf-8") as f:
                json.dump(hooks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error updating hooks library: {e}")
