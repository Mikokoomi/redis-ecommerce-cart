# Chi tiết sản phẩm và xác nhận mua mô phỏng

## Cách chạy và mở

Chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8017
.\.venv\Scripts\python.exe -m pytest -q
```

Nhấn ảnh/tên sản phẩm để mở /#product/SP001. Giỏ tại /#cart, màn hình xác nhận tại /#checkout, kết quả tại /#order/{order_id}. Tham số ?user=... vẫn giữ nguyên. Chỉ màn hình xác nhận gửi POST, có ghi rõ mô phỏng.

## API

- POST /api/cart/{user_id}/checkout, JSON {"confirmed":true,"idempotency_key":"uuid-cua-yeu-cau"}. Không nhận giá từ frontend. Lỗi 400 khi giỏ trống, 409 khi thiếu hàng/sản phẩm mất/dữ liệu vừa thay đổi, 422 khi request sai, 503 khi Redis lỗi.
- GET /api/cart/{user_id}/orders/{order_id}, trả thông tin và giá từng dòng tại thời điểm xác nhận. Kiểm tra user_id khớp đơn; đây chưa phải cơ chế đăng nhập/xác thực.

## Data model

- order:{order_id}: Hash order_id, user_id, total_vnd, status=CONFIRMED_DEMO, created_at (UTC ISO 8601).
- order:{order_id}:items: Hash field product_id, value JSON gồm product_id, product_name, quantity, unit_price_vnd, subtotal_vnd.
- checkout:request:{sha256([user_id,idempotency_key])}: String order_id, giữ kết quả chống trùng.
- Đơn, items và mã chống trùng không đặt TTL. Chính sách giỏ vẫn 86400 giây (24 giờ). Không trừ kho khi thay đổi giỏ, kể cả số lượng vượt kho; chỉ giới hạn 0–99.

## Nguyên tử và chống trùng

WATCH giỏ, mã yêu cầu, key đơn/items và mọi Hash sản phẩm trước khi đọc giá/kho. Kiểm tra tất cả điều kiện trước MULTI; trừ kho, ghi Hash đơn/items, ghi mã chống trùng và xóa giỏ trong cùng EXEC. Xung đột WATCH retry tối đa 8 lần; hết lượt trả 409. Redis mất kết nối trả 503; trạng thái commit có thể chưa rõ với client, nên gửi lại cùng mã yêu cầu.

Nếu mã đã thành công, trả đơn cũ kể cả giỏ hiện tại rỗng hoặc có sản phẩm mới; không trừ kho hoặc xóa giỏ mới. Frontend lưu mã đang gửi trong localStorage trước khi POST, giữ mã khi lỗi/timeout/reload và vô hiệu hóa nút khi đang xử lý. localStorage không chứa giỏ, giá hoặc dữ liệu kết nối. Chỉ xóa mã sau khi nhận thành công. Khi quay lại xác nhận, yêu cầu chưa rõ kết quả có thể gửi lại để lấy đơn cũ.

WATCH/MULTI/EXEC cung cấp tính nhất quán trước các thao tác đồng thời trong Redis standalone. Giả định các key ứng dụng có kiểu dữ liệu đúng và Redis hoạt động bình thường; Redis transaction không có rollback cho lỗi lệnh lúc EXEC (ví dụ sự cố tài nguyên). Không hỗ trợ Redis Cluster nhiều slot trong phiên bản này. Không chỉnh tay key đơn/idempotency trong lúc demo.

## Thực nghiệm Another Redis Desktop Manager

Các thao tác xác nhận thực sự thay đổi stock. Không dùng 20 sản phẩm Cloud để kiểm thử tự động. Khi chủ động demo, ghi số stock trước/sau và số lượng đã xác nhận, không chỉnh dữ liệu để giả kết quả.

```redis
HGET product:SP001 stock
HGETALL cart:demo
TTL cart:demo
# Sau khi chính bạn xác nhận mua trên web:
HGET product:SP001 stock
HGETALL cart:demo
# Sao chép mã đơn thực tế từ màn hình kết quả, thay <order_id>:
HGETALL order:<order_id>
HGETALL order:<order_id>:items
TTL order:<order_id>
```

Kỳ vọng: stock_sau = stock_trước - quantity, giỏ thành công bị xóa, trạng thái CONFIRMED_DEMO, đơn TTL=-1. Giá trong items là snapshot, không đổi theo giá sản phẩm về sau. Khi thiếu hàng, không có stock nào đổi và giỏ giữ nguyên.

## Kết quả xác minh

Toàn bộ pytest: **29 passed, 0 failed, 1 warning** (Starlette/httpx), thời gian 0.89 giây. Python compileall và node --check thành công.

Kiểm thử fakeredis: toàn bộ chức năng cũ, xác nhận một/nhiều sản phẩm, stock, giá hiện tại, snapshot đơn, giỏ rỗng, input sai, thiếu hàng, sản phẩm bị xóa, mất kết nối, retry sau thành công nhưng mất phản hồi, idempotency và hai giao dịch thực sự tranh chấp trước EXEC bằng barrier.

Trình duyệt trên server fakeredis riêng cổng 8018: mở chi tiết, thêm 2 SP001 (kho vẫn 20), xác nhận tổng 9.000.000 đồng, màn hình thành công và reload đơn; mở lại chi tiết kho 18. Thêm 99 rồi xác nhận bị từ chối với tên sản phẩm và lượng kho, không hiển thị thành công. Chi tiết và xác nhận tại 375px không tràn ngang; console error ghi nhận 0. Không chạy checkout trên Redis Cloud.

Giới hạn: không thanh toán tiền thật, đăng nhập hoặc phục hồi dữ liệu sau sự cố Redis. Từ máy/trình duyệt khác muốn retry phải giữ cùng idempotency_key. Giá/kho trên trang xác nhận chỉ là thời điểm tải; Backend luôn kiểm tra lại tại POST.
