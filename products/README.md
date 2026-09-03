# 📦 Thư Mục Quản Lý Mẫu Sản Phẩm (Products)

Thư mục này dùng để điền thông tin sản phẩm gia dụng cần làm video.

---

## 📄 Các file mẫu có sẵn:

1. **`sample_product.json`**: Mẫu điền chi tiết cho 1 sản phẩm:
   - `product_name`: Tên sản phẩm.
   - `key_features`: Các điểm nổi bật (màn hình cảm ứng, công nghệ, thiết kế...).
   - `duration_seconds`: `8` hoặc `10` giây (chuẩn 9:16).
   - `scene_setting`: Bối cảnh quay (bếp, phòng khách, phòng ngủ) và hành động diễn ra.
   - `primary_image`: Ảnh chính của sản phẩm trong thư mục `inputs/`.
   - `custom_prompt`: Prompt chi tiết (nếu có yêu cầu riêng).

2. **`products_batch_template.json`**: Mẫu danh sách nhiều sản phẩm để tạo video hàng loạt.

---

## 💡 Cách dùng nhanh:
- Chỉ cần copy `sample_product.json` thành `ten_san_pham.json`, thay đổi tên sản phẩm & đặt ảnh vào `inputs/`.
- Sau đó bảo trợ lý: *"Tạo video cho sản phẩm trong file products/ten_san_pham.json"*, hệ thống sẽ tự động đọc cấu hình và render qua MCP!
