---
name: video-gia-dung
description: Tiếp nhận ảnh và sản xuất video quảng cáo/review đồ gia dụng TikTok Shop 9:16 qua Telegram và Google Flow Omni Flash, gồm phân tích ảnh bằng vision, duyệt kịch bản, duyệt ảnh, render, QC và gửi MP4. Dùng cho sản phẩm gia dụng; không dùng cho thuốc, thực phẩm chức năng hoặc thiết bị y tế.
---

# Video gia dụng TikTok Shop

Thực hiện quy trình theo từng job độc lập. Agent là bộ phận phân tích và ra quyết định; bot Telegram chỉ nhận/gửi dữ liệu, giữ trạng thái và hiển thị nút duyệt. Không coi kết quả từ template từ khóa là phân tích hình ảnh.

## Trước khi bắt đầu

- Đọc [references/workflow.md](references/workflow.md) cho state machine, điểm dừng duyệt và xử lý lỗi.
- Khi nhận ảnh, đọc [references/image-intake-and-analysis.md](references/image-intake-and-analysis.md).
- Trước khi viết thoại, đọc `rules/tiktok_guidelines.md` từ thư mục gốc repository.
- Trước khi gọi Flow, đọc [references/flow-and-qc.md](references/flow-and-qc.md).
- Dùng duy nhất `models/images/character_portrait.png` làm ảnh nhân vật chuẩn.

## Bất biến bắt buộc

1. Mỗi job thuộc riêng một `chat_id`; không xóa hay ghi đè input/output của job khác.
2. Ảnh sản phẩm phải được Agent mở và phân tích bằng vision. Caption là dữ liệu bổ sung, không thay thế việc nhìn ảnh.
3. Tách rõ thông tin **quan sát được**, **người dùng cung cấp**, và **chưa xác minh**. Không tự bịa công dụng, vật liệu, kích thước hoặc chứng nhận.
4. Luôn dừng để người dùng duyệt kịch bản và ba định hướng bối cảnh trước khi tạo ảnh.
5. Luôn dừng lần hai để người dùng chọn ảnh trước khi render video.
6. Upload ảnh nhân vật và sản phẩm để lấy `media_id` trước khi sinh ảnh. Sinh video chỉ từ `media_id` của ảnh đã duyệt.
7. Không gửi video cuối nếu chưa QC hình, tiếng, thời lượng, khuôn mặt và sản phẩm.
8. Không nói giá cụ thể, không dùng tuyên bố tuyệt đối hoặc công dụng y tế. CTA mặc định: “bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay”.
9. Không tự động retry vô hạn: tối đa 2 lần cho mỗi ảnh/cảnh không đạt; sau đó báo lỗi và xin người dùng chọn hướng xử lý.

## Đầu ra của bước phân tích

Trả về đúng các phần sau để người dùng duyệt:

- Nhận diện sản phẩm và mức độ tin cậy.
- Những chi tiết nhìn thấy trên ảnh.
- Thông tin còn thiếu hoặc chưa xác minh.
- Nỗi đau khách hàng và lợi ích có thể nói an toàn.
- Kịch bản ba cảnh Hook → Công năng/trải nghiệm → CTA; mỗi cảnh 8 hoặc 10 giây tùy độ dài thoại.
- Ba lựa chọn: xưởng/băng chuyền, kho pallet, và bàn kiểm thử hoặc không gian gia đình phù hợp sản phẩm.

Nếu không nhận diện đủ chắc chắn, hỏi đúng một câu ngắn về tên/công dụng sản phẩm và chưa tạo ảnh.

## Khóa prompt hình ảnh

Mọi prompt ảnh phải chứa nguyên văn:

`The exact same Asian woman from reference image 1, strictly preserving 100% of her identical face, identical facial features, identical hairstyle (high bun with parted side hair strands), identical warm smile, and identical skin tone with absolutely zero modifications.`

Và:

`accurate realistic product proportions, perfectly scaled to human body, natural realistic size, not oversized, compact real-world handheld dimensions, perfect anatomical hands and fingers, exactly five natural fingers per hand, natural limbs, no deformed hands, no extra fingers, no missing fingers, no fused fingers, raw authentic real-life commercial photography, realistic natural human skin texture with subtle pores, authentic optical depth of field, real studio and factory lighting, shot on 35mm DSLR lens, photorealistic, no 3D render, no CGI, no anime, no illustration, no plastic airbrushed skin.`

Dùng Medium 3/4 Shot, khoảng cách máy ảnh tương đương 2,5 m, thấy từ thắt lưng lên và có chiều sâu bối cảnh. Có thể đổi trang phục giữa ba option ảnh; sau khi người dùng chọn ảnh, prompt video không được mô tả hoặc thay đổi trang phục nữa.

## Khóa prompt video

Chỉ mô tả chuyển động nhẹ và lời thoại, khóa chặt chất giọng nữ trẻ trung tiếng Việt. Dùng cấu trúc:

`Vertical 9:16 commercial video with native speech audio. The female presenter strictly preserving 100% of her identical face, hairstyle, clothing and holding the exact same product from reference image 1 with zero distortion or morphing. She speaks directly to the camera in a warm, cheerful, friendly young Vietnamese female voice in natural fluent Vietnamese: "{vietnamese_dialogue}" with realistic lip-sync mouth movements, subtle natural breathing, gentle head nods, maintaining the product steady in her hands without changing its appearance or label. Ultra-realistic 4k commercial lighting.`

## Quy trình QC bắt buộc trước khi bàn giao

1. **Duyệt ảnh**: Gửi ảnh 3 Option sang Telegram, CHỜ người dùng xác nhận ưng ý và chọn Option cụ thể. Tuyệt đối không tự ý render video khi người dùng chưa duyệt ưng ảnh.
2. **QC Video trước khi gửi**: Sau khi ghép xong video, Agent phải trực tiếp xem lại video: kiểm tra cử động, khớp khẩu hình tiếng Việt, và thẩm định âm thanh đảm bảo đúng chất giọng nữ ấm áp, chuẩn ngữ điệu, không mất tiếng. Chỉ khi Agent tự xem và ưng ý 100% mới gửi video cho người dùng.

## Hoàn tất

Render ba cảnh 8–10 giây, ghép thành 24–30 giây bằng FFmpeg, QC file cuối rồi gửi MP4 vào đúng cuộc trò chuyện Telegram. Lưu manifest của job gồm input, phân tích, nội dung đã duyệt, media ID, workflow ID, số lần retry và đường dẫn output để có thể tiếp tục sau khi tiến trình khởi động lại.
