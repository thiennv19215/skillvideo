import httpx
import base64
import os
import mimetypes
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FlowClient:
    def __init__(self, base_url: str = "https://api.shopcongngheso5.io.vn"):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(60.0, connect=30.0)

    def encode_image_base64(self, image_path: str) -> tuple[str, str]:
        """Returns (base64_string, mime_type)"""
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return b64, mime_type

    def upload_image(self, image_path: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Uploads an image to Flow and returns media info including 'name' (media_id)"""
        b64, mime_type = self.encode_image_base64(image_path)
        payload = {
            "image_base64": b64,
            "mime_type": mime_type,
            "file_name": os.path.basename(image_path)
        }
        if project_id:
            payload["project_id"] = project_id

        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                res = client.post(f"{self.base_url}/v1/media", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    media_obj = data.get("media") if isinstance(data.get("media"), dict) else data
                    media_id = media_obj.get("name") or data.get("name")
                    logger.info(f"Image uploaded successfully: {image_path} -> {media_id}")
                    return media_obj
                else:
                    logger.error(f"Failed to upload image: {res.status_code} - {res.text}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading image {image_path}: {e}")
            return None

    def generate_image(
        self,
        prompt: str,
        reference_image_paths: Optional[List[str]] = None,
        reference_media_ids: Optional[List[str]] = None,
        aspect_ratio: str = "IMAGE_ASPECT_RATIO_PORTRAIT",
        model: str = "NANO_BANANA_PRO",
        variant_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generates image(s) and returns list of media items"""
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "variant_count": variant_count
        }

        if reference_media_ids:
            payload["reference_media_ids"] = reference_media_ids

        if reference_image_paths:
            input_images = []
            for p in reference_image_paths:
                if os.path.exists(p):
                    b64, mime_type = self.encode_image_base64(p)
                    input_images.append({
                        "image_base64": b64,
                        "mime_type": mime_type,
                        "file_name": os.path.basename(p)
                    })
            if input_images:
                payload["input_images"] = input_images

        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                res = client.post(f"{self.base_url}/v1/images/generations", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    media_list = data.get("media") or data.get("data", {}).get("media", [])
                    for item in media_list:
                        if "downloadUrl" not in item:
                            fife_url = item.get("image", {}).get("generatedImage", {}).get("fifeUrl")
                            if fife_url:
                                item["downloadUrl"] = fife_url
                    return media_list
                else:
                    logger.error(f"Failed to generate image: {res.status_code} - {res.text}")
                    return []
        except Exception as e:
            logger.error(f"Error in generate_image: {e}")
            return []

    def generate_video(
        self,
        prompt: str,
        reference_media_ids: Optional[List[str]] = None,
        reference_image_paths: Optional[List[str]] = None,
        duration_seconds: int = 8,
        aspect_ratio: Optional[str] = None,
        type: str = "omni"
    ) -> Optional[str]:
        """Generates video using Google Flow Omni Flash with strict payload and fail-fast handling"""
        payload: Dict[str, Any] = {
            "type": type,
            "prompt": prompt,
            "duration_seconds": duration_seconds
        }

        if reference_media_ids:
            payload["reference_media_ids"] = reference_media_ids

        try:
            with httpx.Client(timeout=25, trust_env=False) as client:
                res = client.post(f"{self.base_url}/v1/videos/generations", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    workflows = data.get("workflows") or data.get("data", {}).get("workflows", [])
                    if workflows and len(workflows) > 0:
                        op_name = workflows[0].get("name")
                        logger.info(f"Video generation started: {op_name}")
                        return op_name
                    # Alternatively check for operation_name
                    op_name = data.get("operation_name") or data.get("name")
                    return op_name
                else:
                    logger.error(f"Failed to generate video: {res.status_code} - {res.text}")
                    try:
                        err_json = res.json()
                        err_msg = err_json.get("error", {}).get("message", "")
                        if "credit" in err_msg.lower() or "unavailable" in err_msg.lower():
                            print(f"\n⚠️ MÁY CHỦ FLOW THÔNG BÁO: {err_msg}")
                    except Exception:
                        pass
                    return None
        except Exception as e:
            logger.error(f"Error in generate_video: {e}")
            return None

    def get_video_status(self, operation_names: List[str]) -> Dict[str, Any]:
        """Polls video generation status for given operation names"""
        payload = {"operation_names": operation_names}
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                res = client.post(f"{self.base_url}/v1/videos/status", json=payload)
                if res.status_code == 200:
                    return res.json()
                else:
                    logger.error(f"Status check failed: {res.status_code} - {res.text}")
                    return {}
        except Exception as e:
            logger.error(f"Error checking video status: {e}")
            return {}

    def download_file(self, url: str, target_path: str) -> bool:
        """Downloads a remote file and writes to target_path"""
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        try:
            with httpx.Client(timeout=httpx.Timeout(120.0, connect=30.0), trust_env=False) as client:
                res = client.get(url)
                if res.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(res.content)
                    return True
                else:
                    logger.error(f"Failed downloading {url}: {res.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error downloading {url} to {target_path}: {e}")
            return False

    def concat_videos(self, scene_paths: List[str], output_path: str) -> bool:
        """Concatenates video files using ffmpeg"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        concat_list_path = output_path + ".txt"
        try:
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for sp in scene_paths:
                    abs_sp = os.path.abspath(sp).replace("\\", "/")
                    f.write(f"file '{abs_sp}'\n")

            cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c copy "{output_path}"'
            subprocess.run(cmd, shell=True, check=True)
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception as e:
            logger.error(f"Error concatenating videos: {e}")
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            return False
