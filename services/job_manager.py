import os
import time
import uuid
import json
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from services.flow_client import FlowClient
from services.script_generator import ScriptGenerator

logger = logging.getLogger(__name__)

class JobStatus:
    QUEUED = "QUEUED"
    GENERATING_IMAGES = "GENERATING_IMAGES"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    GENERATING_VIDEOS = "GENERATING_VIDEOS"
    CONCATENATING = "CONCATENATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProductJob:
    def __init__(self, job_id: str, chat_id: int, product_name: str, description: str, input_image_path: str):
        self.job_id = job_id
        self.chat_id = chat_id
        self.product_name = product_name
        self.description = description
        self.input_image_path = input_image_path
        self.status = JobStatus.QUEUED
        self.image_options: Dict[str, Dict[str, Any]] = {}
        self.selected_options: List[str] = []
        self.scenes: List[Dict[str, Any]] = []
        self.video_results: Dict[str, str] = {}
        self.error_message: Optional[str] = None
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "chat_id": self.chat_id,
            "product_name": self.product_name,
            "description": self.description,
            "input_image_path": self.input_image_path,
            "status": self.status,
            "image_options": self.image_options,
            "selected_options": self.selected_options,
            "video_results": self.video_results,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class JobManager:
    def __init__(
        self,
        flow_client: FlowClient,
        script_generator: ScriptGenerator,
        model_image_path: Optional[str] = None,
        max_concurrent_jobs: int = 3,
        telegram_callback: Optional[Callable[[str, ProductJob, Any], None]] = None
    ):
        self.flow_client = flow_client
        self.script_generator = script_generator
        self.model_image_path = model_image_path
        self.max_concurrent_jobs = max_concurrent_jobs
        self.telegram_callback = telegram_callback
        self.jobs: Dict[str, ProductJob] = {}
        self.lock = threading.Lock()
        self.executor_threads: List[threading.Thread] = []
        self.running = True

    def set_callback(self, callback: Callable[[str, ProductJob, Any], None]):
        self.telegram_callback = callback

    def create_job(self, chat_id: int, product_name: str, description: str, image_path: str) -> ProductJob:
        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        job = ProductJob(
            job_id=job_id,
            chat_id=chat_id,
            product_name=product_name,
            description=description,
            input_image_path=image_path
        )
        with self.lock:
            self.jobs[job_id] = job
        
        # Start background task for preview generation
        t = threading.Thread(target=self._process_image_generation, args=(job,), daemon=True)
        t.start()
        return job

    def get_job(self, job_id: str) -> Optional[ProductJob]:
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self, chat_id: Optional[int] = None) -> List[ProductJob]:
        with self.lock:
            if chat_id is not None:
                return [j for j in self.jobs.values() if j.chat_id == chat_id]
            return list(self.jobs.values())

    def _notify(self, event: str, job: ProductJob, data: Any = None):
        if self.telegram_callback:
            try:
                self.telegram_callback(event, job, data)
            except Exception as e:
                logger.error(f"Error executing telegram callback for {event}: {e}")

    def _process_image_generation(self, job: ProductJob):
        try:
            job.status = JobStatus.GENERATING_IMAGES
            job.updated_at = time.time()
            self._notify("images_generating", job)

            # Generate scenes script
            job.scenes = self.script_generator.generate_scenes(job.product_name, job.description)
            
            # Prepare reference images
            ref_images = []
            if self.model_image_path and os.path.exists(self.model_image_path):
                ref_images.append(self.model_image_path)
            if job.input_image_path and os.path.exists(job.input_image_path):
                ref_images.append(job.input_image_path)

            prompts_dict = self.script_generator.build_image_prompts(job.product_name)
            output_dir = os.path.join("outputs", job.job_id)
            os.makedirs(output_dir, exist_ok=True)

            for opt_key, opt_data in prompts_dict.items():
                logger.info(f"[{job.job_id}] Generating image for {opt_key}...")
                media_list = self.flow_client.generate_image(
                    prompt=opt_data["prompt"],
                    reference_image_paths=ref_images,
                    aspect_ratio="IMAGE_ASPECT_RATIO_PORTRAIT",
                    variant_count=1
                )

                if media_list and len(media_list) > 0:
                    item = media_list[0]
                    media_name = item.get("name")
                    dl_url = item.get("downloadUrl") or item.get("image", {}).get("downloadUrl")
                    
                    local_img_path = os.path.join(output_dir, f"{opt_key}.jpg")
                    if dl_url:
                        self.flow_client.download_file(dl_url, local_img_path)
                    
                    job.image_options[opt_key] = {
                        "title": opt_data["title"],
                        "media_id": media_name,
                        "download_url": dl_url,
                        "local_path": local_img_path,
                        "prompt": opt_data["prompt"],
                        "environment": opt_data["environment"]
                    }
                else:
                    logger.warning(f"[{job.job_id}] Failed generating image for {opt_key}")

            if job.image_options:
                job.status = JobStatus.WAITING_APPROVAL
                job.updated_at = time.time()
                self._notify("images_ready", job)
            else:
                job.status = JobStatus.FAILED
                job.error_message = "Không thể tạo ảnh mẫu cho sản phẩm. Vui lòng thử lại."
                self._notify("job_failed", job)

        except Exception as e:
            logger.error(f"[{job.job_id}] Error in _process_image_generation: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self._notify("job_failed", job)

    def trigger_video_generation(self, job_id: str, selected_options: List[str]):
        job = self.get_job(job_id)
        if not job:
            return False

        job.selected_options = selected_options
        job.status = JobStatus.GENERATING_VIDEOS
        job.updated_at = time.time()
        self._notify("videos_generating", job)

        t = threading.Thread(target=self._process_video_generation, args=(job,), daemon=True)
        t.start()
        return True

    def _process_video_generation(self, job: ProductJob):
        try:
            output_dir = os.path.join("outputs", job.job_id)
            os.makedirs(output_dir, exist_ok=True)

            for opt_key in job.selected_options:
                opt_info = job.image_options.get(opt_key)
                if not opt_info:
                    continue

                ref_media_id = opt_info.get("media_id")
                env = opt_info.get("environment", "modern manufacturing warehouse")

                scene_workflows = []
                logger.info(f"[{job.job_id}] Starting video generation for {opt_key} (3 scenes)...")
                self._notify("scene_progress", job, {"option": opt_key, "message": f"Bắt đầu khởi tạo 3 cảnh cho {opt_info['title']}..."})

                for scene in job.scenes:
                    v_prompt = self.script_generator.build_video_prompt(scene, job.product_name, env)
                    ref_ids = [ref_media_id] if ref_media_id else None
                    
                    op_name = self.flow_client.generate_video(
                        prompt=v_prompt,
                        reference_media_ids=ref_ids,
                        reference_image_paths=[opt_info["local_path"]] if (not ref_ids and os.path.exists(opt_info.get("local_path", ""))) else None,
                        duration_seconds=scene.get("duration", 8),
                        aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT"
                    )
                    if op_name:
                        scene_workflows.append(op_name)
                    time.sleep(1) # Small stagger

                if len(scene_workflows) < len(job.scenes):
                    logger.error(f"[{job.job_id}] Failed to start all video scenes for {opt_key}")
                    continue

                # Poll until all 3 scenes complete
                max_polls = 60 # Up to 5-10 minutes
                scene_files = []
                all_done = False

                for poll in range(max_polls):
                    time.sleep(8)
                    status_res = self.flow_client.get_video_status(scene_workflows)
                    media_list = status_res.get("media") or status_res.get("data", {}).get("media", [])
                    
                    completed_count = 0
                    current_scene_files = []

                    for idx, m in enumerate(media_list):
                        m_status = m.get("mediaMetadata", {}).get("mediaStatus", {}).get("mediaGenerationStatus")
                        dl_url = m.get("downloadUrl")
                        if m_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL" and dl_url:
                            completed_count += 1
                            scene_p = os.path.join(output_dir, f"{opt_key}_scene{idx+1}.mp4")
                            if not os.path.exists(scene_p):
                                self.flow_client.download_file(dl_url, scene_p)
                            current_scene_files.append(scene_p)
                        elif m_status == "MEDIA_GENERATION_STATUS_FAILED":
                            logger.error(f"[{job.job_id}] Scene {idx+1} failed in {opt_key}")

                    self._notify("scene_progress", job, {
                        "option": opt_key,
                        "completed_scenes": completed_count,
                        "total_scenes": len(job.scenes),
                        "poll": poll + 1
                    })

                    if completed_count == len(job.scenes):
                        all_done = True
                        scene_files = current_scene_files
                        break

                if all_done and len(scene_files) == len(job.scenes):
                    job.status = JobStatus.CONCATENATING
                    final_video_path = os.path.join(output_dir, f"video_{job.product_name}_{opt_key}_24s.mp4".replace(" ", "_"))
                    logger.info(f"[{job.job_id}] Merging {len(scene_files)} scenes into {final_video_path}...")
                    
                    success = self.flow_client.concat_videos(scene_files, final_video_path)
                    if success:
                        job.video_results[opt_key] = final_video_path
                        self._notify("video_ready", job, {"option": opt_key, "video_path": final_video_path})
                    else:
                        logger.error(f"[{job.job_id}] FFmpeg concat failed for {opt_key}")
                else:
                    logger.error(f"[{job.job_id}] Timed out or failed rendering scenes for {opt_key}")

            if job.video_results:
                job.status = JobStatus.COMPLETED
                job.updated_at = time.time()
                self._notify("job_completed", job)
            else:
                job.status = JobStatus.FAILED
                job.error_message = "Kết xuất video thất bại hoặc hết thời gian chờ từ máy chủ Flow."
                self._notify("job_failed", job)

        except Exception as e:
            logger.error(f"[{job.job_id}] Error in _process_video_generation: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self._notify("job_failed", job)
