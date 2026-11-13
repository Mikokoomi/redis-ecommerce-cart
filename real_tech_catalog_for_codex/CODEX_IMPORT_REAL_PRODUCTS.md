# Nhiệm vụ cho Codex: cập nhật 20 sản phẩm thật và ảnh vào RedisCart

## Bối cảnh

- Repo trên Windows: `D:\STUDY\NOSQL`.
- Công nghệ hiện tại: FastAPI, giao diện HTML/CSS/JavaScript, Redis Cloud, Another Redis Desktop Manager.
- Tôi có file `products_real_20.json` chứa 20 sản phẩm công nghệ **có thật**, chia đều 5 danh mục, kèm trang nguồn chính hãng, thông số cơ bản, đường dẫn ảnh sản phẩm và giá **minh họa** (không phải báo giá hiện tại).
- Đường dẫn các ảnh là nguồn tham khảo; cần thực tế tải, xác minh ảnh và lưu thành tài nguyên cục bộ của frontend.

## Yêu cầu bắt buộc

1. **Khảo sát code trước khi sửa**: đọc `backend/seed.py`, `backend/api.py`, các model/service Redis, frontend và test. Xác định chính xác cấu trúc hash `product:*`, set danh mục, key của giỏ, cách render ảnh và giá. Không đoán tên field.
2. **Bảo vệ dữ liệu đang chạy**: không dùng `FLUSHDB`, `FLUSHALL`, `KEYS *` trên Redis Cloud. Không xóa `cart:*`, `order:*`, giỏ mẫu, đơn mẫu và mọi key không thuộc danh mục sản phẩm. Không ghi đè tồn kho đang dùng, nếu sản phẩm có tồn kho thì giữ nguyên; chỉ dùng `stock_demo` khi tạo sản phẩm mới.
3. **Sao lưu catalogue trước khi cập nhật**: chỉ xuất các hash sản phẩm và index danh mục hiện có ra một file JSON backup dưới `docs/backups/` (được Git ignore nếu chứa dữ liệu thật), tránh lộ secret/giỏ/đơn hàng. Có chế độ `--dry-run` hiển thị dự kiến update, không ghi Redis.
4. **Nhập 20 sản phẩm theo định danh cố định `SP001`–`SP020`**. Mỗi item có tên hãng/model thật, mô tả, danh mục, giá minh họa `price_vnd`, thông số `specs`, URL nguồn chính hãng, ảnh `/static/images/products/SPxxx.ext`. Cập nhật index sản phẩm và danh mục theo cấu trúc dự án đang dùng. Không tạo trùng item khi chạy lại.
5. **Ảnh thật**: đọc `image_url` trong JSON, tải ảnh về thư mục static đang được FastAPI phục vụ (có thể thay `image_local` theo route thực tế). Kiểm tra response thành công, Content-Type, giải mã ảnh hợp lệ, kích thước ít nhất 300px chiều ngang nếu khả thi. Chuyển ảnh về `.webp` hoặc `.jpg` dung lượng hợp lý, giữ đúng sản phẩm và không tạo thumbnail SVG giả. Nếu URL 403/404/chống hotlink thì tìm đúng ảnh khác từ hãng/trang sản phẩm, không im lặng để placeholder. Ghi lại nguồn ảnh trong `docs/product-image-sources.md`. Lưu ý ảnh bên thứ ba có thể có bản quyền: dùng nội bộ cho demo học thuật, không tuyên bố có giấy phép thương mại.
6. **Redis chỉ lưu metadata và đường dẫn ảnh**; không ghi binary/base64 vào Redis Cloud Free 30MB. Tham chiếu ảnh local để web hoạt động ổn định và có thể demo offline về phần giao diện (khi ảnh đã được tải).
7. **Chỉ thao tác tồn kho khi thanh toán demo thành công** theo nghiệp vụ đã có. Thêm vào giỏ, mở trang chi tiết, lọc và reload không được trừ stock. Nếu phát hiện implementation hiện tại sai, ghi rõ và sửa/test ở phạm vi cần thiết.
8. **Frontend**: hiển thị ảnh đúng 20 sản phẩm, giá VNĐ, mô tả/thông số trang chi tiết, hỗ trợ lọc 5 danh mục; không phá giao diện hiện tại. Có trạng thái lỗi tải ảnh nếu phát sinh.
9. **Bảo mật**: không in, đưa vào tài liệu, commit hay push `.env`, password, Redis connection URI, token. Nếu `.env.example` vô tình đang chứa secret thật, xóa giá trị bí mật khỏi file mẫu, thay placeholder, và báo cần xoay credential nếu đã từng bị commit/push.
10. **Kiểm thử thực tế**: chạy pytest và smoke test API, kiểm tra Redis Cloud đã nhập đủ 20 hash, 5 danh mục, 20 ảnh cục bộ hiển thị HTTP 200, mở trang chi tiết và thao tác giỏ, thử thanh toán giảm đúng tồn kho. Bài test thay đổi stock/giỏ trên Redis Cloud phải dùng key dùng một lần, sao lưu trước, dọn sạch dữ liệu test an toàn. Không chạy thử checkout lên một giỏ người dùng thật.
11. **Kết quả cuối**: liệt kê các file thay đổi, số sản phẩm nhập thành công, số ảnh tải thành công, số testcase pass/fail, 3 ví dụ key/hash của Redis xem được trên Another Redis Desktop Manager, lỗi/hạn chế còn tồn tại. Sau khi review mới commit, không tự push nếu chưa được yêu cầu.

## Cách nhận dữ liệu

Tôi sẽ đặt `products_real_20.json` ở thư mục gốc `D:\STUDY\NOSQL` trước khi chạy nhiệm vụ này. Nếu file không tồn tại, hãy dừng và báo, không tự dựng sản phẩm giả.

## Tiêu chí hoàn thành

- [ ] 20 tên/model có thật từ file JSON, đúng 5 danh mục.
- [ ] 20 ảnh thật tải về thành công, ảnh đúng model và hiển thị trên frontend.
- [ ] Redis Cloud có metadata và image path, không chứa file ảnh nhị phân.
- [ ] Không có thay đổi không mong muốn lên giỏ/đơn hàng/tồn kho.
- [ ] Test API + UI + Cloud smoke pass, có minh chứng và báo cáo.
