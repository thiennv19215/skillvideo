# Dự Án Video Gia Dụng (FlowProvider MCP)

Hệ thống tự động tạo video quảng cáo / review sản phẩm gia dụng sử dụng **Google Flow (Omni Flash)** thông qua MCP server `flow-provider`.

---

## ⚙️ Cấu Hình Chuẩn (Default Standards)

| Thuộc tính | Giá trị chuẩn | Mô tả |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình (Aspect Ratio)** | `9:16` | Chuẩn video dọc TikTok / YouTube Shorts / Reels |
| **Model Video** | `omni` (Omni Flash) | Sinh video chuyển động chân thực từ ảnh hoặc prompt |
| **Thời lượng (Duration)** | `8` hoặc `10` giây | Tối ưu cho video ngắn giới thiệu sản phẩm |
| **Chất lượng (Quality)** | `lite` / `fast` / `quality` | Mặc định `lite` render nhanh |
| **MCP Server** | `flow-provider` | Kết nối qua `mcp_config.json` |

---

## 📁 Cấu Trúc Thư Mục

```text
video gia dung/
├── config.json              # File cấu hình chuẩn của repo
├── README.md                # Tài liệu hướng dẫn & quy chuẩn
├── inputs/                  # Nơi chứa ảnh sản phẩm đầu vào
├── outputs/                 # Nơi lưu trữ video/ảnh thành phẩm đã tải về
└── prompts/
    └── templates.json       # Kho mẫu prompt chuyên biệt cho đồ gia dụng
```

---

## 🚀 Quy Trình Tạo Video

1. **Chuẩn bị đầu vào**: Đặt ảnh sản phẩm vào thư mục `inputs/` (hoặc yêu cầu AI tạo ảnh nền 9:16 trước).
2. **Gọi MCP Tools**:
   - `flow_upload_image`: Upload ảnh sản phẩm lên hệ thống để lấy `media_id`.
   - `flow_generate_video`: Gửi yêu cầu render video với:
     - `type`: `"omni"`
     - `aspect_ratio`: `"9:16"`
     - `duration_seconds`: `8` hoặc `10`
     - `start_media_id` / `reference_media_ids`: ID ảnh đã upload.
     - `prompt`: Mô tả bối cảnh, chuyển động và công năng sản phẩm.
3. **Theo dõi & Hoàn tất**: Dùng `flow_get_video_status` để lấy link video MP4 và lưu vào `outputs/`.

# skillvideo
