import httpx
import base64
import os
import time
import mimetypes
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FlowClient:
    """Client for FlowProviderAPI (Google Flow Omni Flash & Imagen 3)
    Supports both modern job-based API (/v1/jobs/status, reference_to_video, frames_to_video)
    and backward-compatible proxy contracts.
    """
    def __init__(self, base_url: str = "https://api.shopcongngheso5.io.vn"):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(60.0, connect=30.0)
        self.routing_scope: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.routing_scope:
            headers["X-Provider-Routing-Scope"] = self.routing_scope
        return headers

    def _update_routing_scope(self, res: httpx.Response):
        scope = res.headers.get("x-provider-routing-scope")
        if scope:
            self.routing_scope = scope

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
                res = client.post(f"{self.base_url}/v1/media", json=payload, headers=self._get_headers())
                if res.status_code == 200:
                    self._update_routing_scope(res)
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
        aspect_ratio: str = "9:16",
        model: str = "pro",
        variant_count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generates image(s) using Imagen 3 Pro and returns list of media items.
        Automatically handles modern asynchronous Job polling if returned by FlowProvider.
        """
        # Normalize aspect ratio
        aspect_map = {
            "IMAGE_ASPECT_RATIO_PORTRAIT": "9:16",
            "IMAGE_ASPECT_RATIO_LANDSCAPE": "16:9",
            "IMAGE_ASPECT_RATIO_SQUARE": "1:1"
        }
        normalized_aspect = aspect_map.get(aspect_ratio, aspect_ratio)
        if normalized_aspect not in {"1:1", "16:9", "9:16"}:
            normalized_aspect = "9:16"

        normalized_model = "pro" if "pro" in model.lower() else "v2"

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": normalized_model,
            "aspect_ratio": normalized_aspect,
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
                res = client.post(f"{self.base_url}/v1/images/generations", json=payload, headers=self._get_headers())
                if res.status_code in {200, 202}:
                    self._update_routing_scope(res)
                    data = res.json()
                    
                    # 1. Direct synchronous media response
                    media_list = data.get("media") or data.get("data", {}).get("media", [])
                    if media_list:
                        for item in media_list:
                            if "downloadUrl" not in item:
                                fife_url = item.get("image", {}).get("generatedImage", {}).get("fifeUrl") or item.get("url")
                                if fife_url:
                                    item["downloadUrl"] = fife_url
                        return media_list

                    # 2. Modern Job-based response: {"jobs": [{"id": "...", "status": "queued"}]}
                    jobs = data.get("jobs", [])
                    if jobs:
                        job_id = jobs[0].get("id")
                        logger.info(f"Image job queued: {job_id}. Polling for completion...")
                        for _ in range(30):
                            time.sleep(2)
                            status_res = self.get_video_status([job_id])
                            job_item = next((j for j in status_res.get("jobs", []) if j.get("id") == job_id), None)
                            if job_item:
                                if job_item.get("status") == "complete":
                                    out_media = []
                                    for m in job_item.get("media", []):
                                        url = m.get("url") or m.get("downloadUrl")
                                        out_media.append({
                                            "name": m.get("id"),
                                            "downloadUrl": url,
                                            "url": url
                                        })
                                    return out_media
                                elif job_item.get("status") == "failed":
                                    logger.error(f"Image generation job failed: {job_item.get('error')}")
                                    return []
                        logger.warning(f"Image job {job_id} timed out polling.")
                    return []
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
        start_media_id: Optional[str] = None,
        end_media_id: Optional[str] = None,
        duration_seconds: int = 8,
        aspect_ratio: Optional[str] = None,
        type: str = "reference_to_video"
    ) -> Optional[str]:
        """Generates video using Google Flow Omni Flash.
        Supports:
        - type='reference_to_video' (or 'omni'): multi-reference asset video
        - type='frames_to_video' (or 'frames', 'i2v'): start/end image to video
        Returns job_id or operation_name.
        """
        # Normalize aspect ratio
        aspect_map = {
            "VIDEO_ASPECT_RATIO_PORTRAIT": "9:16",
            "VIDEO_ASPECT_RATIO_LANDSCAPE": "16:9",
            "PORTRAIT": "9:16",
            "LANDSCAPE": "16:9"
        }
        normalized_aspect = aspect_map.get(aspect_ratio, aspect_ratio) if aspect_ratio else "9:16"
        if normalized_aspect not in {"16:9", "9:16"}:
            normalized_aspect = "9:16"

        # Normalize duration (Google Flow supports 4, 6, 8, 10s)
        if duration_seconds not in {4, 6, 8, 10}:
            duration_seconds = 8

        # Normalize type
        is_frames = type in {"frames_to_video", "frames", "start_to_video", "image_to_video", "i2v", "omni_i2v"}
        actual_type = "frames_to_video" if is_frames else "reference_to_video"

        payload: Dict[str, Any] = {
            "type": actual_type,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
            "aspect_ratio": normalized_aspect
        }

        if is_frames:
            actual_start_id = start_media_id
            if not actual_start_id and reference_media_ids:
                actual_start_id = reference_media_ids[0]
            if actual_start_id:
                payload["start_media_id"] = actual_start_id
            if end_media_id:
                payload["end_media_id"] = end_media_id
        else:
            actual_refs = reference_media_ids or []
            if not actual_refs and start_media_id:
                actual_refs = [start_media_id]
            payload["reference_media_ids"] = actual_refs

        try:
            with httpx.Client(timeout=30, trust_env=False) as client:
                res = client.post(f"{self.base_url}/v1/videos/generations", json=payload, headers=self._get_headers())
                if res.status_code in {200, 202}:
                    self._update_routing_scope(res)
                    data = res.json()
                    
                    # 1. Check for modern jobs response: {"jobs": [{"id": "job_123"}]}
                    jobs = data.get("jobs", [])
                    if jobs and len(jobs) > 0:
                        job_id = jobs[0].get("id")
                        logger.info(f"Video generation job submitted: {job_id}")
                        return job_id

                    # 2. Check for workflows response: {"workflows": [{"name": "..."}]}
                    workflows = data.get("workflows") or data.get("data", {}).get("workflows", [])
                    if workflows and len(workflows) > 0:
                        op_name = workflows[0].get("name")
                        logger.info(f"Video generation started (workflow): {op_name}")
                        return op_name
                    
                    op_name = data.get("operation_name") or data.get("name") or data.get("id")
                    return op_name
                else:
                    logger.error(f"Failed to generate video: {res.status_code} - {res.text}")
                    try:
                        err_json = res.json()
                        err_msg = err_json.get("error", {}).get("message", "") or str(err_json)
                        if "credit" in err_msg.lower() or "unavailable" in err_msg.lower():
                            print(f"\n⚠️ MÁY CHỦ FLOW THÔNG BÁO: {err_msg}")
                    except Exception:
                        pass
                    return None
        except Exception as e:
            logger.error(f"Error in generate_video: {e}")
            return None

    def generate_frames_to_video(
        self,
        start_media_id: str,
        prompt: str,
        end_media_id: Optional[str] = None,
        duration_seconds: int = 8,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """Convenience method to generate video from first/last frame"""
        return self.generate_video(
            prompt=prompt,
            start_media_id=start_media_id,
            end_media_id=end_media_id,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            type="frames_to_video"
        )

    def generate_reference_to_video(
        self,
        reference_media_ids: List[str],
        prompt: str,
        duration_seconds: int = 8,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """Convenience method to generate video from reference assets"""
        return self.generate_video(
            prompt=prompt,
            reference_media_ids=reference_media_ids,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            type="reference_to_video"
        )

    def get_video_status(self, job_ids: List[str]) -> Dict[str, Any]:
        """Polls video generation status for given job IDs / operation names.
        Compatible with both modern /v1/jobs/status and legacy /v1/videos/status.
        Returns a normalized dict with 'media' list matching legacy format
        so existing consumers continue working smoothly.
        """
        # Modern endpoint: /v1/jobs/status with {"job_ids": [...]}
        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                res = client.post(
                    f"{self.base_url}/v1/jobs/status",
                    json={"job_ids": job_ids},
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    self._update_routing_scope(res)
                    data = res.json()
                    jobs = data.get("jobs", [])
                    media_list = []
                    for job in jobs:
                        j_status = job.get("status", "running")
                        job_media = job.get("media") or []
                        if j_status == "complete":
                            for m in job_media:
                                url = m.get("url") or m.get("downloadUrl")
                                media_list.append({
                                    "name": m.get("id") or job.get("id"),
                                    "downloadUrl": url,
                                    "url": url,
                                    "mediaMetadata": {
                                        "mediaStatus": {
                                            "mediaGenerationStatus": "MEDIA_GENERATION_STATUS_SUCCESSFUL"
                                        }
                                    }
                                })
                        elif j_status == "failed":
                            media_list.append({
                                "name": job.get("id"),
                                "error": job.get("error"),
                                "mediaMetadata": {
                                    "mediaStatus": {
                                        "mediaGenerationStatus": "MEDIA_GENERATION_STATUS_FAILED"
                                    }
                                }
                            })
                        else:  # queued, running, dispatching
                            media_list.append({
                                "name": job.get("id"),
                                "mediaMetadata": {
                                    "mediaStatus": {
                                        "mediaGenerationStatus": "MEDIA_GENERATION_STATUS_PENDING"
                                    }
                                }
                            })
                    return {
                        "jobs": jobs,
                        "media": media_list,
                        "completed": all(j.get("status") == "complete" for j in jobs) if jobs else False,
                        "failed": any(j.get("status") == "failed" for j in jobs) if jobs else False
                    }
                elif res.status_code in {404, 405}:
                    # Fallback to legacy endpoint /v1/videos/status
                    res_leg = client.post(
                        f"{self.base_url}/v1/videos/status",
                        json={"operation_names": job_ids},
                        headers=self._get_headers()
                    )
                    if res_leg.status_code == 200:
                        return res_leg.json()
                else:
                    logger.error(f"Status check failed: {res.status_code} - {res.text}")
                    return {}
        except Exception as e:
            logger.error(f"Error checking video status: {e}")
            return {}

        return {}

    def download_file(self, url: str, target_path: str) -> bool:
        """Downloads a remote file and writes to target_path"""
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        try:
            with httpx.Client(timeout=httpx.Timeout(180.0, connect=30.0), trust_env=False) as client:
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
