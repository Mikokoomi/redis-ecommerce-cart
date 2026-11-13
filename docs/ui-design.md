# Thiết kế RedisCart

Cập nhật catalogue thật: ảnh SVG riêng đã được thay trong luồng render bằng 20 WebP tải và kiểm tra từ nguồn hãng/nhà bán lẻ; chi tiết có bảng specs và liên kết hãng. Ảnh SVG cũ chỉ giữ để tương thích/fallback, không là ảnh chính. Xem product-image-sources.md và catalog-import.md. Font hiện dùng Be Vietnam Pro được host cục bộ. Các đoạn dưới ghi lại thiết kế ở giai đoạn trước.

Định hướng: cửa hàng công nghệ tối giản, ưu tiên sản phẩm, bố cục Swiss và lưới rõ ràng.

Đã tham khảo hướng dẫn công khai UI UX Pro Max: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill và SKILL.md/references/pro-rules.md. Skill chưa cài trên máy; không chạy script hoặc cài đặt bên thứ ba. Áp dụng hướng dẫn chung về tương phản, focus, nhãn truy cập, nút 44px, ảnh có kích thước dự trữ và responsive; không tuyên bố đã chạy bộ tìm kiếm design system của skill.

## Vấn đề cũ

Banner Navy lớn chiếm màn hình; lưới hẹp do sidebar; biểu tượng ảnh lặp; thiếu tìm kiếm; giỏ hàng thiếu không gian cho thành tiền và tổng kết. Nút số lượng nhỏ, chưa có phản hồi khi yêu cầu đang chạy.

## Hệ thống thiết kế

- Background #F7F8FA, surface #FFFFFF, text #171B24, secondary #667085, border #E7E9ED, accent #CF2E2E, hover #B62525.
- System sans-serif (Segoe UI trên Windows), cỡ chữ theo cấp bậc, dòng 1.5; không cần tải font ngoài.
- Container tối đa 1248px; nhịp khoảng cách 8/16/24/32px, radius 12px; bóng nhẹ khi hover.
- SVG giao diện nét đồng nhất, focus rõ, trạng thái selected có aria-pressed; hỗ trợ reduced motion.
- Lưới 4 cột desktop, 3 cột tablet, 2 cột mobile; giỏ 2 cột desktop và 1 cột mobile.

## Ảnh

20 SVG tự thiết kế tại frontend/assets/products/SP001.svg đến SP020.svg, mỗi sản phẩm có file và hình riêng: điện thoại, laptop, tai nghe không dây/chụp tai/thể thao/có dây, đồng hồ và bốn phụ kiện tương ứng. Đây là hình minh họa vector, không phải ảnh chụp sản phẩm. Ánh xạ bằng product_id; không sửa Redis. Cùng viewBox 320x240, object-fit contain, có fallback và alt text, không phụ thuộc dịch vụ ngoài.

## Điều hướng và dữ liệu

Trang sản phẩm tại /, khu vực giỏ riêng tại /#cart. Tham số ?user=... được giữ qua điều hướng hash. Tìm kiếm tên/mô tả trên dữ liệu API thật, hỗ trợ từ khóa không dấu. Danh mục tiếp tục gọi API category. Giá, tổng tiền, giỏ, TTL vẫn lấy từ Backend; không có localStorage hoặc nguồn sản phẩm giả trong JavaScript.

## Kiểm thử thực tế

- Trình duyệt tải 20 sản phẩm; 5 bộ lọc mỗi loại 4; tìm Study trả 1, từ khóa không tồn tại hiển thị empty state.
- Giỏ codex_smoke_design_2026: thêm Laptop Study 14, tăng 1 lên 2, tổng 25.000.000 đồng; reload giữ số lượng; giảm về 1/tổng 12.500.000; xóa sản phẩm về trống.
- Thêm SP001, mở hộp xác nhận xóa, hủy vẫn giữ tổng 4.500.000; xác nhận xóa toàn bộ về 0. Chỉ dữ liệu thử bị thao tác.
- Kiểm tra sản phẩm và giỏ tại 375, 768, 1024, 1440px không tràn ngang. Product grid tương ứng 2, 3, 3, 4 cột. Ảnh lỗi: 0; console warning/error: 0.
- Điều hướng Tab có focus outline. Đã phát hiện nút submit tìm kiếm chỉ hiển thị với screen reader và sửa thành nút Tìm nhìn thấy được.
- Pytest: 12 passed, 0 failed, 1 cảnh báo Starlette/httpx, 1.39 giây. Node kiểm tra cú pháp JS thành công.

Giới hạn: chưa chạy screen reader, đo contrast tự động toàn trang hoặc mô phỏng mọi lỗi mạng. CSS có prefers-reduced-motion nhưng chưa kiểm tra bằng thay đổi cài đặt hệ điều hành. Không có ảnh chụp before được lưu; screenshot sau đã quan sát trong trình duyệt. Không kiểm thử kho/thanh toán vì ngoài MVP.
