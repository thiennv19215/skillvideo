# 👤 Thư Mục Quản Lý Model (KOL / Reviewer AI)

Thư mục này dùng để lưu trữ thông tin khuôn mặt, phong cách và nhân vật người mẫu AI đóng vai người trải nghiệm hoặc quảng bá đồ gia dụng.

### Cách điền:
1. Tạo một file `.json` mới hoặc copy từ `model_profile_template.json`.
2. Điền các thông tin:
   - `model_id`: Mã định danh mẫu (ví dụ: `nu_review_bep_01`, `nam_review_smart_home_02`).
   - `attributes`: Giới tính, độ tuổi, phong cách trang phục.
   - `reference_images`: Đường dẫn ảnh chân dung của mẫu đặt trong `models/images/`.
   - `prompt_injection`: Đoạn text mô tả mẫu sẽ tự động gắn vào prompt video.
