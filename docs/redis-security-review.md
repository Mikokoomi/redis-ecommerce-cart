# Rà soát feature/redis-updates

Branch đã đồng bộ tracking origin/feature/redis-updates, commit d747ffb5c176eb3dca93c45a3aa2f3c9bc4bf6d7. Các sửa đổi sau đây chưa commit/push.

## Xác thực và nghiệp vụ

Tất cả 8 tuyến giỏ/checkout/buy-now/order yêu cầu current_user từ cookie session và so sánh user_id đường dẫn với user_id phiên. Không cookie/hết phiên trả 401; khác tài khoản trả 403; đơn không thuộc người gọi trả 404. Không có ngoại lệ admin để đọc giỏ người khác. Sản phẩm công khai.

Register không nhận role, luôn tạo customer, mật khẩu PBKDF2-SHA256 và session cookie HttpOnly/SameSite=Lax giữ nguyên. Chuyển setex sang set(ex=...) tương đương để bỏ cảnh báo redis-py.

Frontend xóa ngay nội dung đơn/checkout và giỏ cũ khi đổi tài khoản, đóng hộp xóa giỏ; phản hồi /me khởi động đến muộn không được ghi đè trạng thái đăng nhập mới.

Checkout và mua ngay giữ WATCH/MULTI/EXEC, retry có giới hạn và idempotency theo mode. Mua ngay không xóa giỏ hoặc cập nhật chỉ mục thời gian giỏ; chỉ thêm event. Stock chỉ giảm khi xác nhận thành công, giá snapshot lưu trong đơn.

## Redis key dictionary

| Key | Type | Mục đích / hạn |
| --- | --- | --- |
| product:SPxxx | Hash | Metadata, stock; không TTL |
| products:all | Set | Mã sản phẩm |
| products:category:{slug} | Set | Phân loại |
| user:{id} | Hash | Khách hàng, password_hash không trả API |
| user:email:{email} | String | Email → ID |
| session:{sha256(token)} | String | User ID; TTL 24 giờ |
| cart:{user_id} | Hash | Mã SP → số lượng; TTL 86400 giây |
| carts:updated | Sorted Set | User ID, score Unix time cập nhật giỏ |
| events:cart | Stream | add/update/remove/clear/checkout/buy_now; tối đa 1000 event |
| order:{id} | Hash | Snapshot đơn, không TTL |
| order:{id}:items | Hash | JSON từng dòng hàng, không TTL |
| checkout:request:{hash} | String | Idempotency → đơn; không TTL |

Chỉ mục được cập nhật cùng transaction thay đổi giỏ; clear/checkout xóa member. TTL hoặc xóa field cuối có thể để member tạm thời: backend.cart_activity.recent_carts(db) lọc và dọn bằng WATCH, không xóa giỏ còn tồn tại. Đây là helper quản trị nội bộ, không mở API lộ danh sách giỏ.

## Truy vấn Another Redis Desktop Manager

Lấy user_id của tài khoản kiểm thử đã đăng ký, thay <user_id> và <order_id>:

```redis
HGETALL product:SP001
SMEMBERS products:all
SINTER products:all products:category:dien-thoai
HGETALL cart:<user_id>
TTL cart:<user_id>
ZREVRANGE carts:updated 0 9 WITHSCORES
ZRANGEBYSCORE carts:updated -inf <unix_time>
XLEN events:cart
XREVRANGE events:cart + - COUNT 10
XRANGE events:cart <start_id> <end_id> COUNT 20
HGETALL order:<order_id>
HGETALL order:<order_id>:items
```

Không hiển thị user:* password_hash hoặc session token trong ảnh minh chứng. Event có user_id nên export phải được bảo vệ.

## Import/export và Backup/Restore

Kết nối bằng cấu hình .env tại máy; không export cấu hình kết nối có mật khẩu. Trước khi thao tác, dùng catalogue backup hiện có:

```powershell
.\.venv\Scripts\python.exe -m backend.catalog_import --backup
.\.venv\Scripts\python.exe -m backend.catalog_import --dry-run
```

Backup JSON chỉ catalogue trong docs/backups/ đã Git ignore. Không dùng backup này để khôi phục tài khoản/đơn. Để export qua Manager, chọn chính xác namespace/keys cần thiết, kiểm tra nội dung file và lưu ngoài Git. Khi restore, thử trên database riêng bằng fakeredis hoặc Redis thử nghiệm, đối chiếu kiểu key, JSON và TTL trước; không import đè stock hoặc user/session/order đang dùng. Không dùng lệnh xóa toàn database. Redis Cloud có khả năng backup tùy gói, chưa xác minh gói thực tế; không tuyên bố đã tạo snapshot Cloud.

## Xác minh và giới hạn

Kết quả thực thi: 62 passed, 0 failed, 1 warning Starlette/httpx trong 6.84 giây; compileall Python và node --check cho toàn bộ JavaScript đều thành công. Uvicorn cổng 8017: /, /health, /api/products trả 200, /api/cart/demo không cookie trả 401. Không thực hiện ghi Cloud trong lần kiểm tra HTTP này.

Đã bổ sung kiểm tra và WATCH kiểu key Stream/Sorted Set trước giao dịch ghi. Kiểm thử key Stream sai kiểu trả 503, không trừ stock hoặc xóa giỏ. Scripts smoke Cloud cũ chưa bổ sung đăng nhập, không dùng để kiểm thử API riêng tư sau thay đổi; ưu tiên pytest offline hoặc client có session.

Tests cũ được inject cart_owner trong unit test nghiệp vụ; tests/test_authorization.py chạy auth/session thật với fakeredis, không bỏ qua phân quyền. Có kiểm tra 8 tuyến trả 401/403, đổi tài khoản, session hết hạn, khôi phục giỏ, Stream/Sorted Set, mua ngay và đơn riêng.

Không seed, checkout hay sửa dữ liệu Cloud trong lần rà soát này. Chưa kiểm thử trình duyệt thực tế hoặc mô phỏng network race trong browser. Giao dịch Redis giả định key telemetry đúng kiểu; transaction Redis không rollback runtime error. Rate limiting đăng nhập/đăng ký và hardening CSRF Origin/token là công việc ưu tiên tiếp theo nếu triển khai ra Internet; hiện cookie SameSite=Lax, ứng dụng phục vụ cùng origin. Không merge main/push.
