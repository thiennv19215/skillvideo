import subprocess
import os
from pathlib import Path

frames_dir = Path("sample_videos/extracted_frames")
frames_dir.mkdir(parents=True, exist_ok=True)

videos = list(Path("sample_videos").glob("*.mp4"))
print(f"Found {len(videos)} sample videos:")

for v in videos:
    vid_name = v.stem
    print(f"Extracting frames for {vid_name}...")
    for t in [1, 3, 6, 10]:
        out_frame = frames_dir / f"{vid_name}_t{t}s.jpg"
        cmd = f'ffmpeg -y -ss {t} -i "{v}" -vframes 1 -q:v 2 "{out_frame}"'
        subprocess.run(cmd, shell=True, capture_output=True)
        if out_frame.exists():
            print(f"-> Saved {out_frame} ({out_frame.stat().st_size} bytes)")
