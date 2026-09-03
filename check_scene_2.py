import sys
import json
import httpx
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from services.flow_client import FlowClient

fc = FlowClient()
MEDIA_ID_OPT2 = "5c5995f9-76e6-4839-8d14-f97e3284fd4d"

prompt_scene2 = (
    'Vertical 9:16 commercial video with native speech audio. The female presenter in reference image standing in the logistics warehouse holding the Paris detergent bottle '
    'speaks clearly and confidently to the camera in natural Vietnamese: '
    '"Công nghệ giặt xả hai trong một siêu tiện lợi, đánh bay vết bẩn cứng đầu, kháng khuẩn vượt trội và lưu hương nước hoa thơm ngát gấp ba lần." '
    'Clear audible natural Vietnamese speaking voice, realistic lip-sync mouth movements matching the Vietnamese words, '
    'gentle head nods, smiling warmly, holding the bottle securely at waist level. '
    'Authentic commercial photography lighting, ultra-realistic human skin details.'
)

print("Đang kiểm tra kết nối và gửi lệnh render Cảnh 2...")
payload = {
    "type": "omni",
    "prompt": prompt_scene2,
    "duration_seconds": 8,
    "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
    "reference_media_ids": [MEDIA_ID_OPT2]
}

with httpx.Client(timeout=30, trust_env=False) as client:
    res = client.post(f"{fc.base_url}/v1/videos/generations", json=payload)
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}")
