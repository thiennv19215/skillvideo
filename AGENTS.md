# 🤖 Chỉ Dẫn Hoạt Động Chuẩn Cho AI Agent (Repository: video gia dung)

Tất cả các AI Agent khi làm việc trong repository này **BẮT BUỘC TUÂN THỦ 100%** quy trình kỹ thuật và tiêu chuẩn sản xuất dưới đây:

---

## 🎯 Mục Tiêu Cốt Lõi
Tự động sản xuất video quảng cáo / review đồ gia dụng chuẩn **TikTok Shop (tỉ lệ 9:16, độ dài linh hoạt 24s – 30s với 3 phân cảnh từ 8s đến 10s mỗi cảnh tuỳ theo độ dài câu thoại)** bằng **Google Flow (Omni Flash)** qua MCP `flow-provider` với:
- Nhân vật mẫu AI đồng nhất 100% gương mặt và thần thái.
- Lồng tiếng Việt trực tiếp, khẩu hình nhép môi chân thực.
- Kích thước sản phẩm đúng chuẩn đời thực trên tay.

---

## 📌 10 Quy Tắc Bắt Buộc:

1. **Đồng Nhất Nhân Vật Tuyệt Đối (Character Consistency 100%)**:
   - Luôn sử dụng ảnh chân dung chuẩn tại: `models/images/character_portrait.png` (được crop chuẩn từ `models/images/6a9c56b2-6a6d-46cf-b750-ff898ed99558 (1).png`).
   - **Tuyệt đối KHÔNG thay đổi khuôn mặt / kiểu tóc trong Prompt**:
     Luôn dùng từ khóa cố định:
     `The exact same Asian woman from reference image 1, strictly preserving 100% of her identical face, identical facial features, identical hairstyle (high bun with parted side hair strands), identical warm smile, and identical skin tone with absolutely zero modifications...`

2. **Tiêu Chuẩn Ảnh Chân Thực 100% (Raw Commercial Photography)**:
   - Ảnh tạo ra BẮT BUỘC là ảnh chụp người thật thương mại 100%, da thật tự nhiên có lỗ chân lông và vân da mềm mại, ánh sáng thực tế.
   - **Góc chụp tự nhiên & Không dí sát**: Dùng góc Medium 3/4 Shot (cách 2.5m từ thắt lưng lên), tạo chiều sâu không gian xưởng/kho/phòng giặt.
   - **Tuyệt đối CẤM**: phong cách anime, hoạt hình, vẽ 3D CGI, da sáp mịn bệt như búp bê/bột (`raw authentic real-life commercial photography, realistic natural human skin texture with subtle pores, authentic optical depth of field, real studio and factory lighting, shot on 35mm DSLR lens, photorealistic, no 3D render, no CGI, no anime, no illustration, no plastic airbrushed skin`).

3. **Chuẩn Tỉ Lệ Kích Cỡ Sản Phẩm Đời Thực (Accurate Product Scale)**:
   - Sản phẩm khi cầm trên tay nhân vật hoặc đặt trong bối cảnh phải chuẩn xác tỉ lệ đời thực (ví dụ: vỉ dao cạo ~12cm vừa vặn bàn tay, gối công thái học ~50x30cm cầm vừa 2 tay, can nước giặt 5L ~32cm gọn gàng ngang thắt lưng).
   - Từ khóa bắt buộc: `accurate realistic product proportions, perfectly scaled to human body, natural realistic size, not oversized, compact real-world handheld dimensions`.

4. **Kỹ Thuật Upload Lấy `media_id` Trước Khi Sinh Ảnh/Video Trên Flow Provider**:
   - Khi nhận ảnh từ Telegram, phải tải bản lớn nhất nếu người dùng gửi dạng `photo`; nếu gửi dạng `document` có MIME ảnh thì tải nguyên file và ưu tiên bản này để bảo toàn nhãn/chữ nhỏ. Không được phân loại file ảnh `document` thành video mẫu.
   - AI Agent BẮT BUỘC mở ảnh bằng vision và phân tích trực tiếp. Caption chỉ là thông tin bổ sung; tuyệt đối không coi kết quả từ template/từ khóa là đã phân tích hình ảnh.
   - Báo cáo phải tách rõ: thông tin quan sát được từ ảnh, thông tin người dùng cung cấp, suy luận chưa xác minh và thông tin còn thiếu. Không tự bịa công dụng, vật liệu, kích thước, chứng nhận hoặc xuất xứ.
   - Khi gọi MCP `flow-provider`, BẮT BUỘC upload ảnh qua `flow_upload_image` để lấy `media_id`.
   - Khi gọi `flow_generate_image`, truyền tham số `reference_media_ids: ["<media_id_char>", "<media_id_prod>"]`, `model: "pro"`, `aspect_ratio: "9:16"`.
   - Khi gọi `flow_generate_video`, truyền tham số `reference_media_ids: ["<approved_image_media_id>"]`, `type: "omni"`, `quality: "lite"`, `duration_seconds: 8` (hoặc `10`).

5. **Lồng Thoại Tiếng Việt Trực Tiếp Trong Prompt Video**:
   - Nhúng trực tiếp câu thoại tiếng Việt vào prompt của Omni Flash:
     `...speaks directly to the camera in natural Vietnamese: "{vietnamese_dialogue}" with realistic lip-sync mouth movements...`

6. **Tuân Thủ Chính Sách TikTok Shop & Hạn Chế Nói Về Giá (Price Avoidance)**:
   - Đọc quy chuẩn tại `rules/tiktok_guidelines.md`.
   - Cấm dùng từ: `số 1`, `rẻ nhất`, `tốt nhất`, `cam kết 100%`, `chữa bệnh`, `vĩnh viễn`.
   - **Hạn chế nói về giá**: Tuyệt đối KHÔNG nhắc con số tiền cụ thể (`vài chục cành`, `trăm cành`), không dùng từ `giá sập xưởng`, `không lấy lợi nhuận`.
   - **Tập trung 100% vào**: Nỗi đau khách hàng, giải pháp tiện ích, công năng vượt trội và cảm nhận sử dụng thực tế.
   - CTA hợp lệ: `bấm ngay vào giỏ hàng góc trái màn hình để xem chi tiết và nhận ưu đãi hôm nay`.

7. **Quy Trình Tương Tác 3 Bước (Interactive Agent Workflow)**:
   - **Bước 1 (Phân tích & Soạn kịch bản)**: Khi nhận ảnh sản phẩm từ người dùng, Agent phân tích tính năng, soạn kịch bản 3 cảnh (Hook ➔ Tính năng ➔ CTA) và 3 Option định hướng bối cảnh. Trình bày cho người dùng duyệt trước (KHÔNG tự ý tạo ảnh ngay).
   - **Bước 2 (Tạo 3 Option ảnh duyệt)**: Khi người dùng duyệt, Agent upload media ID và sinh 3 ảnh mẫu 9:16:
     - *Option 1*: Băng chuyền xưởng sản xuất hiện đại (Góc rộng sâu).
     - *Option 2*: Kệ pallet kho hàng cao tầng (Góc rộng sâu).
     - *Option 3*: Bàn kiểm thử / studio phòng giặt gia đình ấm cúng.
   - **Bước 3 (Render Video & Ghép hoàn chỉnh)**: Dùng ảnh duyệt để render các phân cảnh video Omni Flash -> Ghép nối bằng FFmpeg thành video 24s-30s -> Gửi file MP4 hoàn chỉnh cho người dùng qua Telegram.
   - **Điểm dừng bắt buộc**: Chưa duyệt kịch bản thì không tạo ảnh; chưa chọn ảnh thì không render video. Không hiển thị nút “render trực tiếp” trước khi có ảnh đã duyệt.
   - Mỗi job phải thuộc riêng một `chat_id`, có ID không nhập nhằng và trạng thái được lưu bền vững để tiếp tục sau khi bot khởi động lại. Không xóa input/output của job khác.

8. **Tự Chủ & Tư Duy Sáng Tạo Đổi Mới Của AI Agent (Dynamic Tailoring - Không Hardcode)**:
   - **Tuyệt đối KHÔNG dập khuôn kịch bản cứng nhắc (No Hardcoding)**: Mỗi sản phẩm mới gửi vào, Agent BẮT BUỘC phân tích bóc tách các đặc tính thực tế (nỗi đau khách hàng, công năng độc đáo, cách dùng, đối tượng nhắm tới) để sáng tạo ra kịch bản phù hợp riêng cho sản phẩm đó.
   - Luôn đa dạng hóa phong cách Hook (đánh trúng nỗi đau, review đời sống, trải nghiệm mở hộp, quà tặng gia đình...), câu từ tự nhiên, giàu năng lượng và đổi mới liên tục.
   - Mọi khâu bóc tách và thiết kế Prompt đều do AI Agent trực tiếp tư duy dựa trên các file quy chuẩn trong repo (`rules/`, `prompts/`, `skills/`). Tuyệt đối không gọi API bên ngoài trong runtime.

9. **AI Agent Đảm Nhiệm Toàn Diện & Trực Tiếp Giám Sát (End-to-End Direct Monitoring - Không Dựa Dẫm Vào Script)**:
   - **Agent làm chủ toàn bộ vòng đời sản xuất (Full Lifecycle Ownership)**: AI Agent trực tiếp tiếp nhận yêu cầu, điều phối MCP tools (`flow-provider`, FFmpeg, Telegram, v.v.), chủ động kiểm tra (poll/monitor) tiến độ render của từng task ảnh/video và xử lý lỗi phát sinh theo thời gian thực mà không ỷ lại hay dựa dẫm vào các script tự động hóa cứng nhắc bên ngoài.
   - **Trực tiếp kiểm soát chất lượng & phản hồi**: Agent theo dõi sát sao từng giai đoạn, đánh giá kết quả trả về của từng cảnh, tự động tái tạo (retry/refine) nếu xảy ra lỗi hoặc chất lượng không đạt chuẩn trước khi xuất bản video cuối cùng.
   - Agent phải mở và kiểm tra trực quan từng ảnh Option, từng cảnh video và file ghép cuối. Chỉ kiểm tra HTTP/status hoặc file tồn tại là chưa đủ QC.
   - Retry tối đa 2 lần cho mỗi ảnh/cảnh. Nếu vẫn không đạt, giữ manifest, báo rõ tiêu chí thất bại và chờ người dùng quyết định; không retry vô hạn.
   - Manifest mỗi job phải lưu input, phân tích vision, nội dung đã duyệt, media ID, workflow ID theo từng cảnh, số lần retry và đường dẫn output.

10. **Bảo Toàn Tuyệt Đối Nhân Vật & Sản Phẩm Trong Prompt Video (Zero Distortion & Reference Preservation)**:
   - **Tuyệt đối KHÔNG mô tả lại chi tiết mới hay thêm thắt đặc điểm khác lạ trong Prompt Video**: Chỉ tập trung vào chuyển động (Motion), biểu cảm gương mặt tự nhiên, cử chỉ tay nhẹ nhàng và nhép môi khớp câu thoại tiếng Việt.
   - **Khóa cố định đối tượng tham chiếu**: Luôn dùng cấu trúc khóa:
     `Vertical 9:16 commercial video with native speech audio. The female presenter strictly preserving 100% of her identical face, hairstyle, clothing and holding the exact same product from reference image 1 with zero distortion or morphing. She speaks directly to the camera in natural Vietnamese: "{vietnamese_dialogue}" with realistic lip-sync mouth movements, subtle natural breathing, gentle head nods, maintaining the product steady in her hands without changing its appearance or label. Ultra-realistic 4k commercial lighting.`
   - Tránh mọi câu lệnh làm camera lia quá nhanh hoặc chuyển động tay quá mạnh khiến nhãn sản phẩm hoặc ngón tay bị méo mó.

## 🌐 Kiến Trúc Phân Tách Đa Skill (Multi-Skill Architecture):
Repository hỗ trợ mở rộng nhiều ngành hàng với luồng pipeline và quy chuẩn chuyên biệt:
- **Skill 1: Đồ Gia Dụng & Tiện Ích (`video-gia-dung`)**: Bối cảnh xưởng/kho/phòng giặt/bếp, nhân vật nữ trẻ trung năng động, giải quyết nỗi đau sinh hoạt đời sống.
- **Skill 2: Sức Khỏe & TPCN (`video-suc-khoe`)**: Bối cảnh phòng tư vấn/phòng lab/phòng khách gia đình, nhân vật chuyên gia/dược sĩ, tuân thủ nghiêm ngặt chính sách y tế TikTok Shop (cấm từ chữa khỏi/cam kết).
- **Cơ chế kích hoạt**: Agent tự động nhận diện danh mục sản phẩm hoặc người dùng chỉ định để áp dụng đúng Skill tương ứng.

---

## 📚 Tài Liệu Kỹ Thuật Chi Tiết Cho Từng Skill:
- Skill Gia Dụng: `.agents/skills/video-gia-dung/SKILL.md`
- Skill Sức Khỏe: `.agents/skills/video-suc-khoe/SKILL.md`
