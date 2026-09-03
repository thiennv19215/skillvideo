# Nhận và phân tích ảnh Telegram

## Chất lượng file

- `photo`: Telegram cung cấp nhiều kích thước; tải phần tử cuối cùng vì đó là bản lớn nhất, nhưng vẫn có thể đã bị nén.
- `document` có MIME `image/jpeg`, `image/png` hoặc `image/webp`: tải nguyên file, ưu tiên loại này để bảo toàn nhãn, chữ nhỏ và hoa văn.
- `document` không phải ảnh không được đưa vào pipeline sản phẩm.
- Video gửi dưới dạng document chỉ được coi là video mẫu khi MIME hoặc phần mở rộng thực sự là video.

Không upscale ảnh rồi gọi đó là ảnh gốc. Nếu ảnh mờ, phản sáng, mất cạnh hoặc chữ quá nhỏ, yêu cầu người dùng gửi lại dưới dạng file.

## Báo cáo vision bắt buộc

Agent phải thực sự mở ảnh và ghi nhận:

- loại sản phẩm có khả năng nhất và mức tin cậy `cao/trung bình/thấp`;
- màu, hình dáng, số lượng chi tiết/bộ phận nhìn thấy;
- chữ/nhãn đọc được, giữ nguyên chính tả; đánh dấu phần không đọc chắc;
- tỷ lệ ước lượng dựa trên vật tham chiếu nếu có;
- cách cầm hoặc đặt sản phẩm an toàn, tự nhiên;
- dấu hiệu ảnh không đủ để giữ đúng sản phẩm khi sinh ảnh.

## Phân tách nguồn thông tin

- `observed`: trực tiếp nhìn thấy trong ảnh.
- `user_provided`: caption hoặc thông tin người dùng nói.
- `inferred`: suy luận hợp lý nhưng chưa xác minh.
- `unknown`: còn thiếu.

Chỉ dùng `observed` và `user_provided` làm sự thật trong kịch bản. `inferred` phải dùng cách nói dè dặt hoặc hỏi xác nhận. Không suy ra công suất, chất liệu, kích thước, chứng nhận, công dụng sức khỏe hay xuất xứ chỉ từ bao bì mờ.

## Ảnh chuyển sang Flow

- Luôn dùng ảnh sản phẩm rõ nhất làm reference chính.
- Có thể dùng tối đa hai góc bổ sung nếu chúng thể hiện cùng một biến thể sản phẩm.
- Không trộn màu, dung tích hoặc phiên bản khác nhau vào một job nếu người dùng chưa xác nhận.
