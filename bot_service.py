import os
import sys
import time
import json
import logging
import threading
import httpx
from typing import Dict, Any, List, Union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from services.flow_client import FlowClient
from services.script_generator import ScriptGenerator
from services.sample_video_analyzer import SampleVideoAnalyzer

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BotService")

CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("telegram", {}).get("bot_token", "")
if not BOT_TOKEN:
    raise RuntimeError("Thiếu TELEGRAM_BOT_TOKEN hoặc telegram.bot_token trong config.json")
BASE_URL = config.get("mcp_server", {}).get("base_url", "https://api.shopcongngheso5.io.vn")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Model reference image
MODEL_IMG_PATH = None
models_dir = "models/images"
if os.path.exists(os.path.join(models_dir, "character_portrait.png")):
    MODEL_IMG_PATH = os.path.join(models_dir, "character_portrait.png")
elif os.path.exists(models_dir):
    for fn in os.listdir(models_dir):
        if fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            MODEL_IMG_PATH = os.path.join(models_dir, fn)
            break

flow_client = FlowClient(base_url=BASE_URL)
script_gen = ScriptGenerator()
video_analyzer = SampleVideoAnalyzer()

ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
MEDIA_GROUPS: Dict[str, Dict[str, Any]] = {}
MEDIA_TIMERS: Dict[str, threading.Timer] = {}
LOCK = threading.Lock()

# ----------------- TELEGRAM API HELPERS ----------------- #

def send_tg_message(chat_id: int, text: str, reply_markup: dict = None) -> dict:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        with httpx.Client(timeout=20) as client:
            res = client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
            return res.json()
    except Exception as e:
        logger.error(f"send_tg_message error: {e}")
        return {}

def send_tg_photo(chat_id: int, photo_path: str, caption: str = "") -> dict:
    data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
    try:
        with httpx.Client(timeout=60) as client:
            with open(photo_path, "rb") as f:
                res = client.post(f"{TELEGRAM_API}/sendPhoto", data=data, files={"photo": f})
                return res.json()
    except Exception as e:
        logger.error(f"send_tg_photo error: {e}")
        return {}

def send_tg_video(chat_id: int, video_path: str, caption: str = "") -> dict:
    data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}
    try:
        with httpx.Client(timeout=180) as client:
            with open(video_path, "rb") as f:
                res = client.post(f"{TELEGRAM_API}/sendVideo", data=data, files={"video": (os.path.basename(video_path), f, "video/mp4")})
                return res.json()
    except Exception as e:
        logger.error(f"send_tg_video error: {e}")
        return {}

def answer_callback(callback_query_id: str, text: str = ""):
    try:
        with httpx.Client(timeout=10) as client:
            client.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": callback_query_id, "text": text})
    except Exception as e:
        logger.error(f"answer_callback error: {e}")

def download_tg_file(file_id: str, dest_path: str) -> bool:
    try:
        with httpx.Client(timeout=30) as client:
            res = client.get(f"{TELEGRAM_API}/getFile?file_id={file_id}")
            file_path = res.json().get("result", {}).get("file_path")
            if not file_path:
                return False
            dl_res = client.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
            with open(dest_path, "wb") as f:
                f.write(dl_res.content)
            return True
    except Exception as e:
        logger.error(f"download_tg_file error: {e}")
        return False

# ----------------- PIPELINES ----------------- #

def clean_old_stale_products(exclude_job_id: str = ""):
    """Purges all old product folders to prevent stale reference contamination"""
    inputs_dir = "inputs/products"
    if os.path.exists(inputs_dir):
        for item in os.listdir(inputs_dir):
            if item != exclude_job_id:
                p = os.path.join(inputs_dir, item)
                try:
                    if os.path.isdir(p):
                        import shutil
                        shutil.rmtree(p, ignore_errors=True)
                    elif os.path.isfile(p):
                        os.remove(p)
                except Exception as e:
                    logger.warning(f"Error purging old product {p}: {e}")

def generate_option_images_flow(chat_id: int, job_id: str):
    """Triggered ONLY when user explicitly clicks the button to generate 3 option images"""
    try:
        with LOCK:
            job_data = ACTIVE_JOBS.get(job_id)
        if not job_data:
            send_tg_message(chat_id, "❌ Không tìm thấy thông tin sản phẩm.")
            return

        send_tg_message(chat_id, f"🎨 <b>[{job_data['product_name']}]</b>\nĐang tiến hành tạo 3 Option ảnh mẫu 9:16 trên Google Flow... Vui lòng đợi 30s-45s!")
        
        output_dir = job_data["output_dir"]
        prompts = job_data["prompts"]
        ref_images = job_data["ref_images"]

        options_data = {}
        for opt_key, opt_data in prompts.items():
            logger.info(f"[{job_id}] Generating image for {opt_key}...")
            media_list = flow_client.generate_image(
                prompt=opt_data["prompt"],
                reference_image_paths=ref_images[:3],
                aspect_ratio="IMAGE_ASPECT_RATIO_PORTRAIT",
                variant_count=1
            )
            if media_list and len(media_list) > 0:
                m = media_list[0]
                dl_url = m.get("downloadUrl")
                name = m.get("name")
                local_path = os.path.join(output_dir, f"{opt_key}.jpg")
                if dl_url:
                    flow_client.download_file(dl_url, local_path)
                options_data[opt_key] = {
                    "name": name,
                    "downloadUrl": dl_url,
                    "local_path": local_path if os.path.exists(local_path) else None,
                    "title": opt_data["title"],
                    "environment": opt_data.get("environment", "")
                }

        with LOCK:
            job_data["options"] = options_data
            job_data["status"] = "AWAITING_SELECTION"

        # Send 3 options as a single unified Media Group (Album)
        media_group_items = []
        files_to_send = {}
        for idx, opt_key in enumerate(["option_1", "option_2", "option_3"]):
            opt_info = options_data.get(opt_key)
            if not opt_info:
                continue
            lp = opt_info.get("local_path")
            if lp and os.path.exists(lp):
                file_key = f"photo_{idx+1}"
                caption_text = f"📸 <b>{opt_info['title']}</b>"
                media_group_items.append({
                    "type": "photo",
                    "media": f"attach://{file_key}",
                    "caption": caption_text,
                    "parse_mode": "HTML"
                })
                files_to_send[file_key] = open(lp, "rb")

        if media_group_items:
            try:
                with httpx.Client(timeout=60) as client:
                    client.post(
                        f"{TELEGRAM_API}/sendMediaGroup",
                        data={"chat_id": str(chat_id), "media": json.dumps(media_group_items)},
                        files={k: (f"{k}.jpg", v, "image/jpeg") for k, v in files_to_send.items()}
                    )
            except Exception as e_mg:
                logger.error(f"sendMediaGroup error: {e_mg}")
            finally:
                for f in files_to_send.values():
                    f.close()

        markup = {
            "inline_keyboard": [
                [{"text": "1️⃣ Chọn Option 1 (Áo thun / Băng tải)", "callback_data": f"sel_{job_id}_opt1"}],
                [{"text": "2️⃣ Chọn Option 2 (Sơ mi / Kệ kho)", "callback_data": f"sel_{job_id}_opt2"}],
                [{"text": "3️⃣ Chọn Option 3 (Tạp dề / Studio)", "callback_data": f"sel_{job_id}_opt3"}],
                [{"text": "🚀 Tạo Cả 3 Video (Batch Render)", "callback_data": f"sel_{job_id}_all"}]
            ]
        }
        send_tg_message(chat_id, "👇 <b>Bấm chọn Option bạn muốn xuất video:</b>", reply_markup=markup)

    except Exception as e:
        logger.error(f"Error generating option images: {e}", exc_info=True)
        send_tg_message(chat_id, f"❌ Lỗi khi tạo ảnh mẫu: {e}")

def process_product_pipeline(chat_id: int, job_id: str, img_paths: List[str], product_name: str, description: str):
    """Interactive Agent Mode: Analyzes product, builds prompts and scripts, presents to user WITHOUT auto-generating images"""
    try:
        clean_old_stale_products(exclude_job_id=job_id)

        valid_current_imgs = [p for p in img_paths if os.path.exists(p)]
        num_imgs = len(valid_current_imgs)
        output_dir = os.path.join("outputs", job_id)
        os.makedirs(output_dir, exist_ok=True)

        # Build Prompts and Scripts based on repository rules
        prompts = script_gen.build_image_prompts(product_name)
        scenes = script_gen.analyze_and_generate_scenes(product_name, description, product_image_path=valid_current_imgs)

        ref_images = []
        if MODEL_IMG_PATH and os.path.exists(MODEL_IMG_PATH):
            ref_images.append(MODEL_IMG_PATH)
        for p in valid_current_imgs:
            ref_images.append(p)

        with LOCK:
            ACTIVE_JOBS[job_id] = {
                "chat_id": chat_id,
                "job_id": job_id,
                "product_name": product_name,
                "description": description,
                "img_paths": valid_current_imgs,
                "output_dir": output_dir,
                "prompts": prompts,
                "scenes": scenes,
                "ref_images": ref_images,
                "status": "ANALYZED_AWAITING_USER"
            }

        # Format beautiful analysis report for user
        scenes_formatted = "\n".join([f"• <b>Cảnh {s['scene_num']}</b> ({s['name']}):\n  <i>\"{s['dialogue']}\"</i>" for s in scenes])
        
        report_msg = (
            f"🤖 <b>BÁO CÁO PHÂN TÍCH & KỊCH BẢN TỪ AGENT:</b>\n\n"
            f"📦 <b>Sản phẩm:</b> <b>{product_name}</b>\n"
            f"🖼️ <b>Hình ảnh tham chiếu:</b> {num_imgs} ảnh vừa gửi\n\n"
            f"📝 <b>Đề Xuất Kịch Bản 3 Cảnh Chuẩn TikTok Shop (24s):</b>\n{scenes_formatted}\n\n"
            f"🎨 <b>3 Định Hướng Bối Cảnh & Trang Phục (Prompt Ready):</b>\n"
            f"1️⃣ <b>Option 1:</b> Áo thun năng động + Băng tải dây chuyền xưởng\n"
            f"2️⃣ <b>Option 2:</b> Sơ mi pastel + Kho pallet hàng hóa cao tầng\n"
            f"3️⃣ <b>Option 3:</b> Tạp dề hiện đại + Studio bàn test kiểm định\n\n"
            f"👉 <i>Bạn duyệt phương án trên hay muốn tạo ảnh mẫu ngay?</i>"
        )

        markup = {
            "inline_keyboard": [
                [{"text": "🎨 Tạo 3 Option Ảnh Mẫu Duyệt", "callback_data": f"genimgs_{job_id}"}],
                [{"text": "🚀 Render Trực Tiếp Video (Option 1)", "callback_data": f"sel_{job_id}_opt1"}],
                [{"text": "🚀 Render Trực Tiếp Video (Option 2)", "callback_data": f"sel_{job_id}_opt2"}],
                [{"text": "🚀 Render Trực Tiếp Video (Option 3)", "callback_data": f"sel_{job_id}_opt3"}]
            ]
        }

        send_tg_message(chat_id, report_msg, reply_markup=markup)

    except Exception as e:
        logger.error(f"Error in interactive analysis: {e}", exc_info=True)
        send_tg_message(chat_id, f"❌ Lỗi khi phân tích: {e}")

    except Exception as e:
        logger.error(f"Error in product pipeline: {e}", exc_info=True)
        send_tg_message(chat_id, f"❌ Có lỗi khi tạo ảnh mẫu: {e}")

def render_videos_pipeline(chat_id: int, job_id: str, selected_options: list):
    try:
        with LOCK:
            job_data = ACTIVE_JOBS.get(job_id)

        if not job_data:
            send_tg_message(chat_id, "❌ Không tìm thấy thông tin phiên làm việc.")
            return

        product_name = job_data["product_name"]
        options = job_data["options"]
        output_dir = job_data["output_dir"]

        send_tg_message(
            chat_id,
            f"🎬 <b>[{product_name}]</b>\nĐã nhận lựa chọn! Đang khởi tạo các cảnh video Omni Flash (nhúng thoại tiếng Việt và khẩu hình chuẩn)..."
        )

        for opt_key in selected_options:
            opt_info = options.get(opt_key)
            if not opt_info:
                continue

            current_scenes = script_gen.analyze_and_generate_scenes(
                product_name=product_name,
                description=job_data.get("description", ""),
                product_image_path=job_data.get("img_paths"),
                option_key=opt_key
            )
            ref_media_id = opt_info.get("name")
            env = opt_info.get("environment", "modern warehouse factory")

            scene_workflows = []
            send_tg_message(chat_id, f"⚡ Đang bắt đầu kết xuất 3 cảnh cho <b>{opt_info['title']}</b>...")

            for scene in current_scenes:
                v_prompt = script_gen.build_video_prompt(scene, product_name, env)
                ref_ids = [ref_media_id] if ref_media_id else None
                
                op_name = flow_client.generate_video(
                    prompt=v_prompt,
                    reference_media_ids=ref_ids,
                    duration_seconds=scene.get("duration", 8),
                    aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT"
                )
                if op_name:
                    scene_workflows.append(op_name)
                time.sleep(1)

            if len(scene_workflows) < len(current_scenes):
                send_tg_message(chat_id, f"❌ Không thể khởi tạo đủ {len(current_scenes)} cảnh video cho {opt_key}.")
                continue

            # Poll video completion
            max_polls = 60
            scene_files = []
            all_done = False

            for poll in range(max_polls):
                time.sleep(8)
                status_res = flow_client.get_video_status(scene_workflows)
                media_list = status_res.get("media") or status_res.get("data", {}).get("media", [])
                
                completed_count = 0
                current_scene_files = []

                for idx, m in enumerate(media_list):
                    m_status = m.get("mediaMetadata", {}).get("mediaStatus", {}).get("mediaGenerationStatus")
                    dl_url = m.get("downloadUrl")
                    if m_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL" and dl_url:
                        completed_count += 1
                        scene_p = os.path.join(output_dir, f"{opt_key}_scene{idx+1}.mp4")
                        if not os.path.exists(scene_p) or os.path.getsize(scene_p) == 0:
                            flow_client.download_file(dl_url, scene_p)
                        current_scene_files.append(scene_p)

                if (poll + 1) % 3 == 0 or completed_count == len(current_scenes):
                    send_tg_message(
                        chat_id,
                        f"⚡ <b>[{product_name}] - {opt_key}</b>: Đã xử lý xong {completed_count}/{len(current_scenes)} phân cảnh..."
                    )

                if completed_count == len(current_scenes) and len(current_scene_files) == len(current_scenes):
                    all_done = True
                    scene_files = current_scene_files
                    break

            if all_done and len(scene_files) == len(current_scenes):
                final_video_path = os.path.join(output_dir, f"video_{product_name}_{opt_key}_24s.mp4".replace(" ", "_"))
                success = flow_client.concat_videos(scene_files, final_video_path)
                if success:
                    send_tg_message(
                        chat_id,
                        f"✨ <b>[{product_name}]</b> Đã ghép xong video 24s hoàn chỉnh! Đang gửi trực tiếp vào Telegram..."
                    )
                    send_tg_video(
                        chat_id,
                        final_video_path,
                        caption=(
                            f"🎉 <b>Video Thành Phẩm Hoàn Chỉnh (24s - 9:16)</b>\n"
                            f"📦 Sản phẩm: <b>{product_name}</b>\n"
                            f"👗 Phong cách: <b>{opt_key}</b>\n"
                            f"🔊 Thoại tiếng Việt & Khẩu hình tự nhiên 100%\n"
                            f"🛒 Chuẩn chính sách TikTok Shop"
                        )
                    )

                    # Auto-cleanup after successful video delivery
                    try:
                        for sf in scene_files:
                            if os.path.exists(sf):
                                os.remove(sf)

                        img_paths = job_data.get("img_paths", [])
                        for ip in img_paths:
                            if os.path.exists(ip):
                                os.remove(ip)
                        if img_paths:
                            parent_dir = os.path.dirname(img_paths[0])
                            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)

                        logger.info(f"[{job_id}] Cleaned up temporary files and input product images successfully.")
                    except Exception as e_clean:
                        logger.warning(f"Cleanup notice: {e_clean}")

                else:
                    send_tg_message(chat_id, f"❌ Ghép video FFmpeg thất bại cho {opt_key}.")
            else:
                send_tg_message(chat_id, f"❌ Hết thời gian chờ render cho {opt_key}.")

        send_tg_message(
            chat_id,
            f"✅ <b>[{product_name}] ĐÃ HOÀN TẤT & TỰ ĐỘNG DỌN DẸP SẠCH SẼ!</b>\n"
            f"🧹 <i>Đã tự động xóa dữ liệu sản phẩm cũ & file tạm. Bạn có thể gửi sản phẩm tiếp theo bất cứ lúc nào!</i>"
        )

    except Exception as e:
        logger.error(f"Error rendering videos: {e}", exc_info=True)
        send_tg_message(chat_id, f"❌ Có lỗi khi tạo video: {e}")

# ----------------- ALBUM / MULTI-IMAGE COLLECTOR ----------------- #

def flush_media_group(group_key: str):
    with LOCK:
        data = MEDIA_GROUPS.pop(group_key, None)
        MEDIA_TIMERS.pop(group_key, None)
    
    if not data or not data.get("img_paths"):
        return

    chat_id = data["chat_id"]
    job_id = data["job_id"]
    img_paths = data["img_paths"]
    product_name = data["product_name"]
    description = data["description"]

    t = threading.Thread(
        target=process_product_pipeline,
        args=(chat_id, job_id, img_paths, product_name, description),
        daemon=True
    )
    t.start()

# ----------------- MAIN NATIVE POLLING LOOP ----------------- #

def start_native_polling():
    print("==================================================")
    print("🚀 INDESTRUCTIBLE NATIVE TELEGRAM POLLING STARTED!")
    print("==================================================")
    
    offset = 0
    with httpx.Client(timeout=35) as client:
        # Initialize offset to latest on startup to prevent pending conflict
        try:
            res_init = client.get(f"{TELEGRAM_API}/getUpdates?offset=-1", timeout=10)
            if res_init.status_code == 200:
                res_list = res_init.json().get("result", [])
                if res_list:
                    offset = res_list[-1]["update_id"] + 1
                    logger.info(f"Initialized offset to {offset}")
        except Exception as e:
            logger.warning(f"Offset init notice: {e}")

        while True:
            try:
                url = f"{TELEGRAM_API}/getUpdates?offset={offset}&timeout=0" if offset > 0 else f"{TELEGRAM_API}/getUpdates?timeout=0"
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = u["update_id"] + 1
                        
                        # Handle Callback Query (Button clicks)
                        if "callback_query" in u:
                            cb = u["callback_query"]
                            cb_id = cb["id"]
                            cb_data = cb.get("data", "")
                            chat_id = cb["message"]["chat"]["id"]
                            answer_callback(cb_id, "Đã nhận lựa chọn!")

                            parts = cb_data.split("_")
                            if len(parts) >= 2 and parts[0] == "genimgs":
                                job_id = "_".join(parts[1:])
                                t = threading.Thread(target=generate_option_images_flow, args=(chat_id, job_id), daemon=True)
                                t.start()

                            elif len(parts) >= 3 and parts[0] == "sel":
                                job_id = parts[1]
                                choice = parts[2]
                                selected = []
                                if choice == "opt1": selected = ["option_1"]
                                elif choice == "opt2": selected = ["option_2"]
                                elif choice == "opt3": selected = ["option_3"]
                                elif choice == "all": selected = ["option_1", "option_2", "option_3"]

                                t = threading.Thread(target=render_videos_pipeline, args=(chat_id, job_id, selected), daemon=True)
                                t.start()

                        # Handle Messages
                        elif "message" in u:
                            msg = u["message"]
                            chat_id = msg["chat"]["id"]
                            sender = msg.get("from", {}).get("first_name", "Bạn")

                            # 1. Photo Message (Album / Single / Multi-photo)
                            # 1. Photo Message or Document Image
                            is_photo_msg = "photo" in msg
                            is_doc_image = False
                            doc_obj = msg.get("document")
                            if doc_obj:
                                mime = doc_obj.get("mime_type", "").lower()
                                fname = doc_obj.get("file_name", "").lower()
                                if mime.startswith("image/") or fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
                                    is_doc_image = True

                            if is_photo_msg or is_doc_image:
                                if is_photo_msg:
                                    photos = msg["photo"]
                                    largest_photo = photos[-1]
                                    file_id = largest_photo["file_id"]
                                else:
                                    file_id = doc_obj["file_id"]

                                caption = msg.get("caption", "").strip()
                                # Single User-level group key for seamless batching
                                group_key = f"user_{chat_id}"

                                with LOCK:
                                    if group_key not in MEDIA_GROUPS:
                                        job_id = f"prod_{int(time.time())}"
                                        input_dir = os.path.join("inputs", "products", job_id)
                                        os.makedirs(input_dir, exist_ok=True)
                                        
                                        p_name = caption.split("\n")[0].strip() if caption else "Sản phẩm gia dụng cao cấp"
                                        p_desc = "\n".join(caption.split("\n")[1:]).strip() if "\n" in caption else caption

                                        MEDIA_GROUPS[group_key] = {
                                            "chat_id": chat_id,
                                            "job_id": job_id,
                                            "input_dir": input_dir,
                                            "img_paths": [],
                                            "product_name": p_name,
                                            "description": p_desc
                                        }

                                    group_data = MEDIA_GROUPS[group_key]
                                    img_idx = len(group_data["img_paths"]) + 1
                                    dest_img = os.path.join(group_data["input_dir"], f"product_image_{img_idx}.jpg")
                                    
                                    if caption and group_data["product_name"] == "Sản phẩm gia dụng cao cấp":
                                        group_data["product_name"] = caption.split("\n")[0].strip()
                                        group_data["description"] = "\n".join(caption.split("\n")[1:]).strip() if "\n" in caption else caption

                                if download_tg_file(file_id, dest_img):
                                    with LOCK:
                                        group_data["img_paths"].append(dest_img)
                                        # Reset / start debounce timer (2.0s)
                                        if group_key in MEDIA_TIMERS:
                                            MEDIA_TIMERS[group_key].cancel()
                                        timer = threading.Timer(2.0, flush_media_group, args=(group_key,))
                                        MEDIA_TIMERS[group_key] = timer
                                        timer.start()

                            # 2. Video Message (Sample video learning)
                            elif "video" in msg or (doc_obj and not is_doc_image):
                                v = msg.get("video") or doc_obj
                                file_id = v["file_id"]
                                file_name = v.get("file_name", f"sample_{int(time.time())}.mp4")
                                caption = msg.get("caption", "")

                                send_tg_message(chat_id, "⏳ <b>Đã nhận Video Mẫu!</b> Đang tự động trích xuất khung hình & học hỏi kịch bản/bối cảnh...")
                                os.makedirs("sample_videos", exist_ok=True)
                                local_video_path = os.path.join("sample_videos", file_name)

                                if download_tg_file(file_id, local_video_path):
                                    learned = video_analyzer.analyze_and_learn_from_video(local_video_path, caption_hint=caption)
                                    send_tg_message(
                                        chat_id,
                                        f"🎓 <b>ĐÃ HỌC THÀNH CÔNG TỪ VIDEO MẪU!</b>\n\n"
                                        f"📌 <b>Phong cách:</b> <b>{learned.get('name')}</b>\n"
                                        f"🎣 <b>Ý tưởng Hook học được:</b> <i>\"{learned.get('hook_concept')}\"</i>\n"
                                        f"🏛️ <b>Bối cảnh:</b> {learned.get('environment_desc')}\n"
                                        f"👗 <b>Trang phục:</b> {learned.get('outfit_desc')}\n"
                                        f"⚡ <b>Nhịp điệu:</b> {learned.get('pacing')}\n\n"
                                        f"💾 <i>Đã lưu vào <b>Kho Template Mẫu</b> để tự động áp dụng cho các sản phẩm tiếp theo!</i>"
                                    )
                                else:
                                    send_tg_message(chat_id, "❌ Lỗi khi tải video mẫu.")

                            # 3. Text Message (Chat)
                            elif "text" in msg:
                                text = msg["text"].strip()
                                print(f"[CHAT] {sender}: {text}")
                                if text.startswith("/start"):
                                    send_tg_message(chat_id, "👋 Xin chào! Gửi <b>ảnh sản phẩm + thông số</b> để tạo video 24s, hoặc gửi <b>video mẫu</b> để tôi học hỏi kịch bản nhé!")
                                else:
                                    send_tg_message(chat_id, f"👌 Đã nhận: \"{text}\". Hãy gửi ảnh sản phẩm để tôi bắt đầu làm video nhé!")

                    time.sleep(1.5)
                else:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Polling loop exception: {e}")
                time.sleep(2)

if __name__ == "__main__":
    start_native_polling()
