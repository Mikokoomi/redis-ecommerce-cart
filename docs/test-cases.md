# Kiểm thử MVP

Sau nhập catalogue thật: **46 passed, 0 failed, 1 warning, 1.31 giây**. Thêm kiểm thử dry-run không ghi, backup đúng namespace, import lặp lại, giữ stock=0/stock thay đổi đồng thời, không thay đổi giỏ/đơn, kiểu dữ liệu sai và xác minh 20 WebP. Cloud smoke đạt trên sản phẩm/giỏ dùng một lần; stock riêng 5→2, gửi lại không trừ lần hai; 5 key thử đã dọn. API trả 20 sản phẩm, 5 danh mục và 20 ảnh HTTP 200. Chi tiết tại catalog-import.md.

Lần chạy sau bổ sung checkout: **29 passed, 0 failed, 1 warning, 0.89 giây**. Cú pháp Python và JavaScript hợp lệ. Kiểm thử mua mô phỏng dùng fakeredis; không trừ kho trên Cloud. Chi tiết tại checkout.md. Server Cloud sau cập nhật: /health và /health/redis trả 200, OpenAPI có endpoint checkout.

Đã chạy pytest với fakeredis: **12 passed, 0 failed**. Năm giá trị số lượng không hợp lệ được pytest tham số hóa thành năm trường hợp.

Đã thực thi: seed 20 Hash, 5 Set danh mục, sản phẩm không có TTL; seed lại bảo toàn dữ liệu; seed 4 giỏ và giữ giỏ cũ; danh sách/lọc/chi tiết; thêm và cộng dồn; giới hạn 99; cập nhật và xóa bằng 0; xóa một/toàn giỏ; tổng tiền; đọc lại giỏ; TTL được làm mới; sản phẩm không tồn tại; từ chối giá do client gửi; Redis mất kết nối và không lộ nội dung lỗi; phục vụ HTML/CSS/JS/SVG.

Kiểm thử tích hợp Redis Cloud đã thực thi: PING thành công; seed tạo mới 20 sản phẩm, 5 danh mục (4 sản phẩm/danh mục), 4 giỏ mẫu. Kiểm tra Hash sản phẩm, Set danh mục và products:all; sản phẩm không có TTL. Bốn giỏ mẫu là Hash, TTL quan sát 1780 giây tại thời điểm kiểm tra.

Server Uvicorn thực tế tại cổng 8017: /, /health, /health/redis, /api/products, /api/products/SP001, /api/products?category=dien-thoai, /api/cart/demo, CSS và JS đều trả 200. Script backend.smoke_cloud đối chiếu Redis sau từng thao tác thêm, cộng dồn, cập nhật, xóa, đọc lại, tính tổng từ giá Redis và kiểm tra TTL; chỉ xóa key thử UUID của lần chạy. Tất cả thành công.

Pytest chạy lại: 12 passed, 0 failed, 1 warning trong 0.61 giây. Cảnh báo Starlette về httpx là cảnh báo tương thích công cụ kiểm thử, không ảnh hưởng kết quả lần chạy hoặc luồng ứng dụng; chưa nâng cấp thư viện để xử lý cảnh báo.

Trình duyệt thực tế: hiển thị 20 sản phẩm và ảnh, lọc Laptop còn 4 sản phẩm, đọc giỏ Cloud. Trên giỏ codex_smoke_ui_6e85: thêm SP001 (4.500.000 đồng), tăng lên 2 (9.000.000 đồng), reload giữ 2, giảm về 1, xóa về giỏ trống. Không có console error được ghi nhận. Đã thêm tham số user trên URL để chọn giỏ thử riêng và phiên bản URL JS tránh cache cũ. Trong bước đầu kiểm thử trình duyệt dùng cache cũ đã tăng SP001 của demo; đã đặt lại đúng số lượng 2 ngay sau đó (TTL demo được làm mới).

Chưa kiểm thử tải đồng thời, chờ đủ 1800 giây để quan sát hết hạn thực, mọi kích thước mobile, toàn bộ 5 nút lọc bằng trình duyệt, hộp xác nhận xóa toàn bộ và tương tác trực tiếp Another Redis Desktop Manager. API xóa toàn giỏ đã kiểm thử Cloud; cả 5 danh mục đã kiểm thử bằng fakeredis.

Kiểm tra demo thủ công: seed Cloud, mở trang trên desktop/mobile, lọc 5 danh mục, thêm sản phẩm trùng, tăng/giảm/xóa, reload và quan sát giỏ giữ lại, xác nhận xóa toàn bộ, quan sát Hash/Set/TTL trong Another Redis Desktop Manager.
