import os
import sys
import json
import shutil
import webbrowser
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="Video Gia Dung Studio", description="Desktop UI for TikTok Shop Video Production")

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Ensure essential directories exist
MODELS_IMG_DIR = BASE_DIR / "models" / "images"
INPUTS_PROD_DIR = BASE_DIR / "inputs" / "products"
PRODUCTS_JSON_DIR = BASE_DIR / "products"
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "ui" / "static"
TEMPLATES_DIR = BASE_DIR / "ui" / "templates"

for d in [MODELS_IMG_DIR, INPUTS_PROD_DIR, PRODUCTS_JSON_DIR, OUTPUTS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Mount static and media directories
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/media/models", StaticFiles(directory=str(MODELS_IMG_DIR)), name="models_media")
app.mount("/media/inputs", StaticFiles(directory=str(BASE_DIR / "inputs")), name="inputs_media")
app.mount("/media/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs_media")

# Helper to read config
def load_config():
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>UI Template not found</h1>", status_code=404)

@app.get("/api/system/status")
async def get_system_status():
    config = load_config()
    
    # Active character
    char_portrait = MODELS_IMG_DIR / "character_portrait.png"
    has_active_char = char_portrait.exists()
    char_mtime = datetime.fromtimestamp(char_portrait.stat().st_mtime).strftime("%d/%m/%Y %H:%M") if has_active_char else None
    
    # Character history
    char_files = []
    for f in MODELS_IMG_DIR.glob("*.*"):
        if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            char_files.append({
                "filename": f.name,
                "url": f"/media/models/{f.name}",
                "is_active": f.name == "character_portrait.png",
                "size_kb": round(f.stat().st_size / 1024, 1),
                "updated_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            })
    
    # Products count
    products_count = len(list(PRODUCTS_JSON_DIR.glob("*.json")))
    
    # Outputs count
    outputs_images = len(list(OUTPUTS_DIR.glob("**/*.png"))) + len(list(OUTPUTS_DIR.glob("**/*.jpg")))
    outputs_videos = len(list(OUTPUTS_DIR.glob("**/*.mp4")))

    return {
        "project_name": config.get("project_name", "video_gia_dung"),
        "has_active_character": has_active_char,
        "character_info": {
            "name": "Mẫu Nữ Chuẩn (Asian Young Host)",
            "portrait_url": "/media/models/character_portrait.png" if has_active_char else None,
            "updated_at": char_mtime,
            "total_images": len(char_files),
            "files": char_files
        },
        "stats": {
            "products_count": products_count,
            "outputs_images": outputs_images,
            "outputs_videos": outputs_videos
        },
        "config": config.get("defaults", {})
    }

@app.post("/api/character/upload")
async def upload_character(file: UploadFile = File(...), set_as_default: bool = Form(True)):
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in [".png", ".jpg", ".jpeg", ".webp"]:
            raise HTTPException(status_code=400, detail="Định dạng file không hỗ trợ. Hãy tải ảnh PNG, JPG hoặc WEBP.")

        timestamp = int(time.time())
        original_name = f"character_source_{timestamp}{suffix}"
        backup_path = MODELS_IMG_DIR / original_name
        
        # Save original/uploaded file
        with open(backup_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Set as default portrait
        if set_as_default:
            target_path = MODELS_IMG_DIR / "character_portrait.png"
            shutil.copyfile(backup_path, target_path)

        return {
            "success": True,
            "message": "Tải lên ảnh nhân vật thành công!",
            "portrait_url": "/media/models/character_portrait.png",
            "filename": original_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/character/set-active")
async def set_active_character(filename: str = Form(...)):
    source_path = MODELS_IMG_DIR / filename
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="File không tồn tại")
    
    target_path = MODELS_IMG_DIR / "character_portrait.png"
    shutil.copyfile(source_path, target_path)
    return {"success": True, "message": f"Đã đặt {filename} làm nhân vật mẫu mặc định!"}

@app.post("/api/products/create")
async def create_product(
    name: str = Form(...),
    category: str = Form("Đồ gia dụng"),
    scale_desc: str = Form(""),
    key_features: str = Form(""),
    pain_points: str = Form(""),
    target_audience: str = Form(""),
    notes: str = Form(""),
    images: List[UploadFile] = File(...)
):
    try:
        product_slug = "".join([c if c.isalnum() else "_" for c in name.lower()]).strip("_")
        timestamp = int(time.time())
        product_id = f"{product_slug}_{timestamp}" if product_slug else f"prod_{timestamp}"
        
        # Create product image directory
        prod_img_dir = INPUTS_PROD_DIR / product_id
        prod_img_dir.mkdir(parents=True, exist_ok=True)
        
        saved_images = []
        for idx, img in enumerate(images):
            if not img.filename:
                continue
            suffix = Path(img.filename).suffix.lower()
            if suffix not in [".png", ".jpg", ".jpeg", ".webp"]:
                continue
            img_name = f"image_{idx+1}{suffix}"
            img_path = prod_img_dir / img_name
            with open(img_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            saved_images.append({
                "filename": img_name,
                "url": f"/media/inputs/products/{product_id}/{img_name}",
                "path": str(img_path.relative_to(BASE_DIR)).replace("\\", "/")
            })
            
        if not saved_images:
            raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất 1 ảnh sản phẩm hợp lệ.")

        # Build product data structure
        product_data = {
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "scale_description": scale_desc or "Kích thước tiêu chuẩn đời thực, cầm vừa vặn trên tay",
            "key_features": [f.strip() for f in key_features.split("\n") if f.strip()],
            "pain_points": [p.strip() for p in pain_points.split("\n") if p.strip()],
            "target_audience": target_audience or "Khách hàng gia đình, người nội trợ, thanh niên",
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "images": saved_images,
            "primary_image": saved_images[0]["url"]
        }

        # Save product JSON
        json_path = PRODUCTS_JSON_DIR / f"{product_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "message": f"Đã lưu sản phẩm '{name}' thành công!",
            "product": product_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/list")
async def list_products():
    products = []
    for f in PRODUCTS_JSON_DIR.glob("*.json"):
        if f.name in ["products_batch_template.json"]:
            continue
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                products.append(data)
        except Exception:
            pass
    products.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"products": products}

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str):
    json_path = PRODUCTS_JSON_DIR / f"{product_id}.json"
    img_dir = INPUTS_PROD_DIR / product_id
    
    if json_path.exists():
        json_path.unlink()
    if img_dir.exists():
        shutil.rmtree(img_dir, ignore_errors=True)
        
    return {"success": True, "message": f"Đã xoá sản phẩm {product_id}"}

@app.get("/api/outputs/list")
async def list_outputs():
    images = []
    videos = []
    
    for f in OUTPUTS_DIR.glob("**/*.*"):
        if f.is_file():
            rel_path = str(f.relative_to(OUTPUTS_DIR)).replace("\\", "/")
            stat = f.stat()
            item = {
                "filename": f.name,
                "path": rel_path,
                "url": f"/media/outputs/{rel_path}",
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            }
            if f.suffix.lower() in [".mp4", ".mov", ".webm"]:
                videos.append(item)
            elif f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                images.append(item)
                
    videos.sort(key=lambda x: x["created_at"], reverse=True)
    images.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"images": images, "videos": videos}

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"
    print("=" * 60)
    print(f"Video Gia Dung Studio UI dang chay tai: {url}")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
