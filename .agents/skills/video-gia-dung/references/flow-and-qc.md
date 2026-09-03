# Flow Provider và kiểm soát chất lượng

## Thứ tự gọi

1. Upload `models/images/character_portrait.png` và lấy `media_id_character`.
2. Upload ảnh sản phẩm chính, cùng ảnh bổ sung nếu cần, và lấy media ID.
3. Tạo ba ảnh với `reference_media_ids`, `model: "pro"`, `aspect_ratio: "9:16"`.
4. Sau khi người dùng chọn ảnh, lấy `approved_image_media_id`.
5. Tạo từng cảnh video với `type: "omni"`, `quality: "lite"`, `aspect_ratio: "9:16"`, `duration_seconds: 8` hoặc `10`, và `reference_media_ids: [approved_image_media_id]`.

Không truyền ảnh bằng base64 trực tiếp nếu quy trình Flow hiện hành yêu cầu media ID.

## QC ảnh Option

Agent mở từng ảnh và kiểm tra:

- đúng khuôn mặt, tóc và sắc da của ảnh nhân vật;
- ảnh người thật, da tự nhiên, không CGI;
- đúng sản phẩm, màu, hình dáng và nhãn chính;
- kích thước hợp lý so với bàn tay/cơ thể;
- ngón tay, cạnh sản phẩm và chữ không méo nghiêm trọng;
- bố cục dọc 9:16, Medium 3/4 Shot, bối cảnh có chiều sâu;
- không có chữ quảng cáo bịa thêm hoặc vật thể thừa gây hiểu sai.

## QC video cảnh

- file mở được và có cả video stream lẫn audio stream;
- thời lượng khớp 8 hoặc 10 giây với dung sai hợp lý;
- khuôn mặt, tóc, trang phục và sản phẩm không morph;
- nhãn không đổi; tay không dị dạng rõ rệt;
- giọng Việt nghe rõ, lời đúng kịch bản đã duyệt;
- khẩu hình tương đối khớp, không cắt mất câu;
- không có chuyển động máy hoặc tay quá mạnh.

## QC file ghép

- tỉ lệ 9:16, tổng 24–30 giây;
- đúng thứ tự ba cảnh;
- âm thanh không mất, không lệch rõ rệt và không có khoảng đen giữa cảnh;
- FFmpeg concat bằng stream copy chỉ khi codec/thông số các cảnh tương thích; nếu không, chuẩn hóa về H.264 + AAC rồi ghép;
- chạy kiểm tra kỹ thuật cuối trước khi gửi Telegram.

Nếu lỗi chỉ thuộc một cảnh, tạo lại đúng cảnh đó. Sau hai lần không đạt, giữ kết quả và báo cụ thể tiêu chí thất bại để người dùng quyết định.
