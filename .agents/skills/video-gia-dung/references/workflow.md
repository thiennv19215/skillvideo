# State machine vận hành

Mỗi job dùng khóa ổn định, ví dụ `<chat_id>-<timestamp>-<random>`, và được lưu bền vững. Không chỉ lưu trong biến RAM.

## Trạng thái

1. `RECEIVING_MEDIA`
   - Gom ảnh thuộc cùng album Telegram.
   - Chấp nhận `photo` và file ảnh gửi dưới dạng `document`.
   - Kiểm tra MIME, kích thước, khả năng mở file và hash chống trùng.

2. `ANALYZING`
   - Agent mở tất cả ảnh bằng vision.
   - Ưu tiên ảnh gốc; chọn một ảnh chính và tối đa hai ảnh bổ sung.
   - Tạo báo cáo phân tích và kịch bản, không gọi Flow.

3. `AWAITING_SCRIPT_APPROVAL`
   - Gửi báo cáo, ba cảnh và ba định hướng bối cảnh.
   - Nút hợp lệ: `Duyệt & tạo 3 ảnh`, `Sửa kịch bản`, `Hủy`.
   - Không cung cấp nút render trực tiếp ở trạng thái này.

4. `GENERATING_OPTIONS`
   - Upload ảnh nhân vật và ảnh sản phẩm để lấy media ID.
   - Tạo đúng ba ảnh Option 9:16.
   - Theo dõi từng tác vụ và retry tối đa 2 lần nếu lỗi kỹ thuật hoặc QC không đạt.

5. `AWAITING_IMAGE_APPROVAL`
   - Agent QC ba ảnh trước khi gửi.
   - Gửi ảnh kèm nhãn Option 1/2/3.
   - Nút hợp lệ: chọn một Option, tạo lại một Option, quay lại sửa kịch bản, hủy.

6. `RENDERING`
   - Render ba cảnh chỉ từ ảnh đã duyệt.
   - Lưu mapping `scene_number → workflow_id` thay vì dựa vào thứ tự response.
   - Poll có backoff; không gửi tin nhắn trạng thái liên tục khi không có thay đổi.

7. `QUALITY_CHECK`
   - Tải từng cảnh, kiểm tra rồi ghép.
   - Nếu một cảnh lỗi, chỉ tạo lại cảnh đó; không tạo lại toàn bộ job.

8. `COMPLETED`
   - Gửi MP4 vào đúng `chat_id`.
   - Giữ input, manifest và output theo chính sách lưu trữ; không xóa dữ liệu của job khác.

9. `FAILED` hoặc `CANCELED`
   - Ghi nguyên nhân và bước cuối cùng có thể tiếp tục.

## Tính nhiều người dùng

- Mọi callback Telegram phải chứa hoặc tra cứu toàn bộ job ID một cách không nhập nhằng; không tách ID bằng dấu gạch dưới rồi lấy vị trí cố định.
- Xác minh người bấm callback có cùng `chat_id`/user được phép sở hữu job.
- Áp dụng `allowed_users` trước khi tải file hoặc gọi Flow.
- Giới hạn số job đồng thời theo cấu hình nhưng không xóa input của job đang chạy.

## Điểm dừng và retry

- Chưa duyệt kịch bản: không tạo ảnh.
- Chưa chọn ảnh: không render video.
- Mỗi asset được retry tối đa 2 lần.
- Nếu hết credit, xác thực lỗi, Flow không khả dụng hoặc hai lần retry vẫn hỏng: chuyển `FAILED`, giữ manifest và báo người dùng.
