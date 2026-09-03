import os
import re
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

BANNED_TIKTOK_WORDS = [
    "số 1", "so 1", "rẻ nhất", "re nhat", "tốt nhất", "tot nhat",
    "cam kết 100%", "cam ket 100%", "chữa bệnh", "chua benh",
    "vĩnh viễn", "vinh vien", "tuyệt đối", "tuyet doi",
    "vài chục cành", "vai chuc canh", "trăm cành", "tram canh",
    "giá sập sàn", "gia sap san", "giá sập xưởng", "gia sap xuong",
    "không lấy một đồng lợi nhuận", "khong lay mot dong loi nhuan",
    "rẻ như cho", "re nhu cho"
]

class ScriptGenerator:
    def __init__(self, api_key: Optional[str] = None):
        logger.info("Initialized ScriptGenerator with 100% local repository template and file rules.")

    def clean_tiktok_policy(self, text: str) -> str:
        """Removes or replaces banned words and excessive price claims under TikTok Shop policy"""
        result = text
        for banned in BANNED_TIKTOK_WORDS:
            pattern = re.compile(re.escape(banned), re.IGNORECASE)
            result = pattern.sub("cực kỳ chất lượng", result)
        return result

    def analyze_product_category(self, product_name: str, description: str) -> Dict[str, Any]:
        """Dynamically identifies product domain, key pain points, and killer features"""
        combined = f"{product_name} {description}".lower()

        # 1. Personal Care / Shaving / Grooming
        if any(k in combined for k in ["dao cạo", "cạo râu", "lưỡi dao", "gillette", "tỉa lông", "dao cao"]):
            return {
                "category": "grooming",
                "pain_point": "cạo râu hay bị rát đỏ, trầy xước hoặc dùng dao cùn khó chịu",
                "core_benefit": "cạo cực sát êm ái, bảo vệ làn da mịn màng không kích ứng",
                "key_features": "lưỡi dao kép chống ma sát, đầu xoay linh hoạt ôm sát đường cong và dải gel bôi trơn làm dịu da",
                "target_audience": "các anh nam giới hoặc chị em mua tặng chồng",
                "props": "cầm gọn vỉ dao cạo trên tay hoặc kiểm thử góc cạo"
            }
        
        # 2. Bedding / Ergonomic / Wellness
        elif any(k in combined for k in ["gối", "cong thai hoc", "công thái học", "cổ vai gáy", "ngủ ngon", "ruột gối"]):
            return {
                "category": "wellness",
                "pain_point": "ngủ dậy hay bị đau mỏi cổ vai gáy, gối xẹp lún mất form",
                "core_benefit": "nâng đỡ đốt sống cổ chuẩn y khoa, giúp giấc ngủ sâu và êm ái",
                "key_features": "chất liệu cao su non đàn hồi chậm, thiết kế rãnh công thái học ôm trọn vùng gáy",
                "target_audience": "dân văn phòng, người lớn tuổi và cả gia đình",
                "props": "dùng 2 tay ôm vừa vặn chiếc gối, ấn thử độ đàn hồi mềm mại"
            }

        # 3. Kitchen / Cooking Appliances
        elif any(k in combined for k in ["nồi", "chảo", "nấu", "bếp", "chiên", "lẩu", "hấp", "ấm", "bình"]):
            return {
                "category": "kitchen",
                "pain_point": "nấu ăn mất nhiều thời gian, đồ ăn dễ cháy dính khó cọ rửa",
                "core_benefit": "nấu nướng nhanh gọn tiện lợi, chống dính an toàn vệ sinh",
                "key_features": "lòng nồi phủ men chống dính cao cấp, gia nhiệt nhanh đều và dung tích nhỏ gọn thông minh",
                "target_audience": "các bạn sinh viên, người ở trọ hoặc gia đình nhỏ",
                "props": "mở nắp nồi hoặc giơ chiếc nồi nhỏ gọn trên mặt bàn"
            }

        # 4. Cleaning / Home Organization
        elif any(k in combined for k in ["lau nhà", "chổi", "hút bụi", "kệ", "tủ", "hộp", "giặt"]):
            return {
                "category": "cleaning",
                "pain_point": "dọn dẹp nhà cửa tốn sức, bụi bẩn ngóc ngách khó lau sạch",
                "core_benefit": "nhà cửa sạch bóng tinh tươm trong tích tắc, tiết kiệm thời gian dọn dẹp",
                "key_features": "thiết kế trợ lực thông minh, khớp xoay linh hoạt và chất liệu bền bỉ",
                "target_audience": "mọi gia đình và người nội trợ hiện đại",
                "props": "thao tác thử sản phẩm gọn gàng, giới thiệu chi tiết từng khớp nối"
            }

        # 5. General Smart Household (Default Dynamic)
        else:
            feat = description if description and len(description) > 15 else "thiết kế nhỏ gọn, đa năng tiện ích, chất liệu bền bỉ đạt chuẩn"
            return {
                "category": "smart_home",
                "pain_point": "cuộc sống bận rộn cần giải pháp tiện ích để tối ưu thời gian",
                "core_benefit": "mang lại sự tiện nghi, hiện đại và nâng tầm không gian sống",
                "key_features": feat,
                "target_audience": "mọi gia đình hiện đại",
                "props": "cầm trên tay sản phẩm vừa vặn, giới thiệu chi tiết sản phẩm"
            }

    def analyze_and_generate_scenes(
        self,
        product_name: str,
        description: str = "",
        product_image_path: Optional[Any] = None,
        option_key: str = "option_1"
    ) -> List[Dict[str, Any]]:
        """Generates 3 dynamic, non-hardcoded TikTok Shop scenes tailored to the specific product info"""
        
        p_name = product_name.strip() if product_name and product_name.strip() else "Sản phẩm gia dụng cao cấp"
        analysis = self.analyze_product_category(p_name, description)

        pain = analysis["pain_point"]
        benefit = analysis["core_benefit"]
        features = analysis["key_features"]

        # 3 Creative Scenarios tailored to environments
        if option_key == "option_1":
            # Bối cảnh Xưởng sản xuất (Dây chuyền băng tải)
            scene1_dialogue = f"Đang có mặt trực tiếp tại dây chuyền sản xuất để cùng cả nhà khám phá chiếc {p_name} chính hãng cực kỳ tiện lợi này đây ạ!"
            scene2_dialogue = f"Sản phẩm giải quyết triệt để nỗi lo {pain}. Với {features}, chiếc {p_name} này giúp {benefit} một cách tối ưu nhất."
            scene3_dialogue = f"Một sản phẩm thiết thực cho cả gia đình, mọi người bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay nhé!"
            action_1 = "holding product proudly at modern factory conveyor, gesturing enthusiastically"
            
        elif option_key == "option_2":
            # Bối cảnh Kho pallet cao tầng (Giải quyết nỗi đau trực tiếp)
            scene1_dialogue = f"Ai đang gặp tình trạng {pain} thì dừng lại ba giây xem ngay giải pháp chân ái {p_name} này nha!"
            scene2_dialogue = f"Điểm ưng ý nhất chính là {features}, vừa bền đẹp vừa giúp {benefit} mỗi ngày."
            scene3_dialogue = f"Sản phẩm chính hãng đã sẵn sàng tại kho, mọi người nhanh tay bấm ngay vào giỏ hàng góc trái để nhận ưu đãi phiên này nha!"
            action_1 = "holding product gracefully in warehouse aisle, speaking warmly to camera"

        else:
            # Bối cảnh Studio kiểm thử / Review trải nghiệm cận cảnh
            scene1_dialogue = f"Cùng em mở hộp và trải nghiệm thực tế chiếc {p_name} thông minh đang được rất nhiều gia đình tin dùng này nhé!"
            scene2_dialogue = f"Cảm nhận thực tế trên tay cực kỳ ưng ý: {features}, hỗ trợ {benefit} nhẹ nhàng và tiện lợi."
            scene3_dialogue = f"Một món đồ nhỏ gọn nâng cấp không gian sống, các bác bấm ngay vào giỏ hàng góc trái màn hình để sở hữu ngay nhé!"
            action_1 = "holding product with both hands at studio testing workbench, smiling radiantly"

        return [
            {
                "scene_num": 1,
                "name": "Cảnh 1 (Hook mở đầu)",
                "dialogue": self.clean_tiktok_policy(scene1_dialogue),
                "duration": 8,
                "action": action_1
            },
            {
                "scene_num": 2,
                "name": "Cảnh 2 (Công năng & Trải nghiệm)",
                "dialogue": self.clean_tiktok_policy(scene2_dialogue),
                "duration": 8,
                "action": "demonstrating product features smoothly, smiling warmly, holding product clearly"
            },
            {
                "scene_num": 3,
                "name": "Cảnh 3 (CTA Giỏ hàng)",
                "dialogue": self.clean_tiktok_policy(scene3_dialogue),
                "duration": 8,
                "action": "pointing gently down to bottom left corner, inviting viewer warmly"
            }
        ]

    def build_image_prompts(self, product_name: str) -> Dict[str, Dict[str, str]]:
        """Generates 3 distinct image option prompts strictly enforcing character face consistency and product identity"""
        character_anchor = (
            "The exact same female presenter from reference image 1, maintaining 100% identical facial features, same face structure, "
            "same eye shape, same eyebrows, same nose, same lips, and natural warm Asian skin tone, "
        )
        product_anchor = (
            f"holding the exact {product_name} from reference image 2 with identical color, fabric texture, and pattern, "
            f"accurate realistic product proportions, perfectly scaled to human body, natural realistic size, not oversized, "
        )
        base_quality = (
            "raw authentic real-life commercial photography, realistic natural human skin texture with subtle pores, "
            "authentic optical depth of field, real studio and factory lighting, shot on 35mm DSLR lens, photorealistic, "
            "no 3D render, no CGI, no anime, no illustration, no plastic airbrushed skin, 9:16 vertical ratio."
        )

        options = {
            "option_1": {
                "title": "Option 1: Áo thun năng động + Dây chuyền băng tải xưởng",
                "outfit": "wearing a clean white modern casual t-shirt",
                "environment": "modern clean factory assembly conveyor belt background with neatly arranged production units",
                "prompt": (
                    f"{character_anchor}smiling warmly, hair tied neatly, wearing a clean white modern casual t-shirt, "
                    f"standing inside a bright modern manufacturing factory. {product_anchor}"
                    f"In the background, neat factory conveyor line packaging rows of this product. {base_quality}"
                )
            },
            "option_2": {
                "title": "Option 2: Sơ mi pastel + Kệ kho hàng cao tầng pallet",
                "outfit": "wearing an elegant light pastel blue button-up shirt",
                "environment": "spacious organized modern distribution warehouse with high storage pallet racks",
                "prompt": (
                    f"{character_anchor}with elegant friendly demeanor, wearing an elegant light pastel blue button-up shirt, "
                    f"standing in a spacious modern distribution warehouse. {product_anchor}"
                    f"Behind her are high industrial storage racks neatly stacked with inventory cartons. {base_quality}"
                )
            },
            "option_3": {
                "title": "Option 3: Tạp dề phong cách / Polo + Bàn kiểm thử studio xưởng",
                "outfit": "wearing a stylish minimalist beige kitchen apron over a dark polo top",
                "environment": "clean studio testing workbench inside a modern smart home quality test lab",
                "prompt": (
                    f"{character_anchor}with radiant friendly expression, wearing a stylish modern beige apron over a dark polo top, "
                    f"standing in a bright testing studio. {product_anchor}"
                    f"No text on product, warm bright professional studio lighting. {base_quality}"
                )
            }
        }
        return options

    def build_video_prompt(self, scene: Dict[str, Any], product_name: str, option_env: str = "bright modern factory warehouse") -> str:
        """Builds Omni Flash prompt strictly preserving character face identity, product appearance, and embedding Vietnamese dialogue"""
        dialogue = scene["dialogue"]
        action = scene.get("action", "speaks directly to camera")
        
        prompt = (
            f"Vertical 9:16 commercial video with native speech audio. "
            f"The female presenter strictly preserving 100% of her identical face, hairstyle, clothing and holding the exact same {product_name} from reference image 1 with zero distortion or morphing. "
            f"She {action}, speaks directly and enthusiastically to the camera in natural Vietnamese: \"{dialogue}\". "
            f"Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, "
            f"subtle natural breathing, gentle head nods, maintaining the product steady in her hands without changing its appearance or label. "
            f"Ultra-realistic 4k commercial lighting, cinematic depth."
        )
        return prompt
