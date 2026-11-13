# Redis E-Commerce Cart

Catalogue hiện tại đã nhập từ real_tech_catalog_for_codex/products_real_20.json: 20 model thật, 5 danh mục, 20 ảnh WebP cục bộ. Giá trong file là giá minh họa, không phải báo giá thị trường đã xác minh. Chi tiết thao tác và kết quả tại docs/catalog-import.md; nguồn ảnh tại docs/product-image-sources.md.

Để nhập lại (giữ nguyên stock và dữ liệu giỏ/đơn):

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m backend.catalog_import --backup
.\.venv\Scripts\python.exe -m backend.catalog_import --dry-run
.\.venv\Scripts\python.exe -m backend.catalog_import --apply
```

Importer mặc định dry-run; --apply luôn sao lưu catalogue trước. Dùng importer này cho catalogue hiện tại. backend.seed là fixture mẫu cũ cho kiểm thử, không chạy --update của seed để thay catalogue thật.

Đã bổ sung chi tiết sản phẩm và mua hàng mô phỏng có trừ kho nguyên tử, lưu đơn và chống gửi trùng. Xem [hướng dẫn checkout](docs/checkout.md) để biết API, mô hình Redis, kiểm thử và cách demo bằng Another Redis Desktop Manager.

Đề tài: Tìm hiểu Another Redis Desktop Manager để quản trị và khai thác Redis trong quản lý giỏ hàng thương mại điện tử.

MVP dùng FastAPI, redis-py, Redis Cloud và HTML/CSS/JavaScript thuần. Dữ liệu sản phẩm lấy từ Redis; dữ liệu mẫu chỉ nằm trong script seed. Stock được kiểm tra và trừ khi xác nhận mua mô phỏng thành công.

## Cấu trúc
```text
backend/ main.py, api.py, config.py, redis_client.py, seed.py
         requirements.txt, requirements-dev.txt
frontend/ index.html, css/style.css, js/app.js, assets/*.svg
tests/ test_mvp.py
redis/ commands.md, seed.redis
docs/ architecture.md, test-cases.md
.env.example
.gitignore
```

## Chạy trên Windows
```powershell
cd D:\STUDY\NOSQL
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Điền REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD, REDIS_SSL trong .env theo Redis Cloud. Không chia sẻ mật khẩu; file .env được Git bỏ qua. TLS đặt true khi endpoint yêu cầu. Biến môi trường ưu tiên hơn .env.

```powershell
.\.venv\Scripts\python.exe -m backend.seed --carts
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Seed tạo 20 sản phẩm thuộc 5 danh mục và tùy chọn 4 giỏ mẫu (2 sản phẩm/giỏ). Chạy lại bỏ qua bản ghi đã tồn tại. Chỉ dùng --update khi cần cập nhật sản phẩm mẫu; script yêu cầu nhập CAP NHAT, không cập nhật giỏ cũ. Không chạy lệnh xóa toàn database.

Mở http://127.0.0.1:8000/; tài liệu API tại /docs; kiểm tra /health và /health/redis. Nếu Redis chưa cấu hình hoặc mất kết nối, API dữ liệu trả 503; Backend và trang vẫn khởi động được. Giao diện dùng giỏ demo, tải lại trang sẽ đọc lại Redis.

## API
| Method | Đường dẫn | Chức năng |
| --- | --- | --- |
| GET | /api/products?category=dien-thoai | Danh sách hoặc lọc theo danh mục |
| GET | /api/products/{product_id} | Chi tiết |
| GET | /api/cart/{user_id} | Giỏ, tổng tiền, tổng số lượng, TTL |
| POST | /api/cart/{user_id}/items | Body product_id, quantity; cộng dồn |
| PATCH | /api/cart/{user_id}/items/{product_id} | Body quantity; đặt số lượng |
| DELETE | /api/cart/{user_id}/items/{product_id} | Xóa sản phẩm |
| DELETE | /api/cart/{user_id} | Xóa giỏ |

Quantity là số nguyên 0–99; 0 xóa sản phẩm. Giá luôn lấy từ Hash sản phẩm. Thay đổi giỏ làm mới TTL 86400 giây (24 giờ); giỏ trống không có key. Mỗi giỏ độc lập theo user_id. Đây là demo không có đăng nhập, không dùng user_id làm cơ chế bảo mật.

## Kiểm thử
```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend
```
fakeredis chỉ dùng trong kiểm thử; không ghi vào Cloud. Xem docs/test-cases.md để biết kết quả và giới hạn kiểm thử.

Đã xác nhận Redis Cloud: 20 sản phẩm, 5 danh mục, 4 giỏ mẫu tại thời điểm seed. Giỏ tự hết hạn sau 86400 giây (24 giờ). Pytest: 12 passed, 0 failed, 1 warning. CRUD Cloud và các thao tác giỏ cơ bản qua trình duyệt đã chạy thành công.

Để chạy lại kiểm thử tích hợp chủ động, mở server ở cổng 8017 rồi chạy:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8017
# Trong cửa sổ PowerShell khác tại thư mục repository:
.\.venv\Scripts\python.exe -m backend.smoke_cloud
```

Script kiểm tra dữ liệu đã seed và tạo/xóa đúng một giỏ codex_smoke_ có UUID. Trên giao diện có thể mở /?user=codex_smoke_ten_rieng để dùng giỏ riêng; đây không phải cơ chế xác thực.

## Data model và quản trị
Xem docs/architecture.md và redis/commands.md. Trong Another Redis Desktop Manager tạo kết nối bằng cùng host, port, username, password và SSL của Redis Cloud, chọn database 0, kết nối rồi refresh key. Không chia sẻ ảnh chụp chứa mật khẩu.
