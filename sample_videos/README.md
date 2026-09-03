# 🎬 Thư Mục Video Mẫu (Sample Videos)

Thư mục này dùng để chứa các video mẫu bạn muốn AI phân tích và sao chép bối cảnh / góc quay / kịch bản thoại.

---

## 🔄 Luồng làm việc 3 Bước:

### Bước 1: Nạp Video Mẫu & Phân Tích
- Bạn thả video mẫu vào `sample_videos/` hoặc gửi video/link cho AI.
- AI sẽ tự động phân tích:
  1. **Bối cảnh & Góc quay & Tư thế nhân vật**: Xác định khung cảnh, ánh sáng, góc máy và cách nhân vật tương tác với đồ gia dụng.
  2. **Kịch bản Lời thoại (Voiceover)**: Viết lại lời thoại cho sản phẩm mới với **độ dài chuẩn 8s đến 10s** (khoảng 20–35 từ tiếng Việt, ngắt nhịp tự nhiên).
  3. **Prompt tạo ảnh**: Sinh prompt kết hợp **nhân vật của bạn** + **bối cảnh tương tự** + **sản phẩm mới**.

---

### Bước 2: Tạo Ảnh & Duyệt (User Approval)
- AI sẽ sinh ảnh dọc `9:16` giữ đúng khuôn mặt nhân vật từ `models/images/` và sản phẩm từ `inputs/`.
- AI gửi ảnh cho bạn xem trước.
- **Bạn duyệt**: Nếu cần chỉnh sửa góc máy / tư thế thì yêu cầu AI chỉnh lại; nếu hài lòng, bạn chỉ cần gõ **"OK"** hoặc **"Duyệt"**.

---

### Bước 3: Tạo Video Omni Flash (8s - 10s)
- Ngay sau khi bạn duyệt "OK", AI sẽ dùng ảnh đã chọn làm frame gốc và gọi MCP `flow_generate_video` (Omni Flash, 9:16, 8-10s).
- Video hoàn thiện cùng file kịch bản khớp thời gian sẽ được lưu vào thư mục `outputs/`.
