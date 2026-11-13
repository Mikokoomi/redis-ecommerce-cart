# Nhập catalogue 20 sản phẩm thật

Đã đọc toàn bộ CODEX_IMPORT_REAL_PRODUCTS.md và products_real_20.json trong real_tech_catalog_for_codex/. Dữ liệu gốc được giữ nguyên. Dùng file này ở thư mục con đã tìm thấy, không dựng sản phẩm thay thế.

## Các bước đã chạy

1. Đọc seed, API, service Redis, checkout, frontend và tests. Hash product:SPxxx, index products:all và products:category:{slug}; giỏ cart:{user}, đơn order:{id}/items.
2. Sao lưu catalogue cũ tại docs/backups/catalog-20261113T191559842062Z.json (UTC trong tên file). Bản ngay trước lần import đầu: catalog-20261113T192113665148Z.json. Có thêm backup trước smoke và lần cập nhật nguồn ảnh. Chỉ có Hash/Set catalogue, không chứa giỏ/đơn hoặc cấu hình kết nối; docs/backups/ được Git ignore.
3. Tải và giải mã 20 ảnh, chuyển WebP, tạo manifest SHA-256. Một URL DNS lỗi và hai URL 403 đã thay bằng nguồn hãng; thêm thay ảnh gallery Logitech/UGREEN để đúng trang sản phẩm. Xem product-image-sources.md.
4. Dry-run: 20 update, 20 stock preserved, không ghi Redis.
5. Apply: 20 update trong WATCH/MULTI/EXEC; sao lưu tự động trước mỗi lần apply. Chỉ HSET metadata; không gửi field stock nếu đã tồn tại. Index được thêm/sửa trong namespace catalogue; không xóa giỏ/đơn hoặc key khác.
6. Đối chiếu: 20 Hash, products:all có 20 member, 5 Set danh mục mỗi Set 4. Stock 20 sản phẩm khớp trước nhập; 3 key giỏ/đơn/idempotency hiện có khớp digest nội dung, không key TTL nào biến mất trong lần đối chiếu cuối.
7. Chạy lại dry-run cuối: 20 unchanged; không tạo trùng.

## Chạy lại

```powershell
cd D:\STUDY\NOSQL
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
# Chỉ cần tải lại khi ảnh thiếu hoặc đổi nguồn:
.\.venv\Scripts\python.exe tools\fetch_product_images.py
.\.venv\Scripts\python.exe -m backend.catalog_import --backup
.\.venv\Scripts\python.exe -m backend.catalog_import --dry-run
.\.venv\Scripts\python.exe -m backend.catalog_import --apply
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8017
```

Có thể truyền --input đường dẫn JSON. Thiếu input/ảnh/manifest hoặc sai kiểu dữ liệu sẽ dừng. Cần Pillow và httpx trong requirements-dev. Không chạy seed --update của fixture cũ sau khi nhập catalogue thật.

## Bảo toàn và xử lý đồng thời

Importer WATCH các Hash đích, products:all và Set danh mục trước khi đọc. Chỉ ghi metadata, giữ cả field tùy chỉnh; stock đã có (kể cả 0) được giữ nguyên. Stock chỉ khởi tạo từ stock_demo khi field chưa có. Nếu stock cũ không hợp lệ thì dừng, không tự sửa. Nếu checkout làm đổi stock giữa lúc đọc và EXEC thì retry tối đa 8 lượt, không đưa stock cũ trở lại.

Không dùng FLUSHDB/FLUSHALL/KEYS. Backup dùng SCAN theo product:* và products:category:*; chỉ đọc products:all cụ thể. Các Set danh mục cũ giữ member ngoài SP001–SP020. Sản phẩm và index catalogue không TTL.

Giỏ hiện có vẫn tham chiếu SP001–SP020 nên sẽ hiển thị tên/giá mới khi đọc API; số lượng giỏ giữ nguyên. Đơn cũ có snapshot tên/giá riêng nên không đổi.

## Kiểm thử thực tế

- Pytest: 46 passed, 0 failed, 1 warning Starlette/httpx trong 1.31 giây. Python compileall và node --check thành công.
- Cloud HTTP: 20 danh sách/chi tiết khớp JSON, cả 5 bộ lọc 4 sản phẩm; 20/20 ảnh trả 200 và giải mã WebP hợp lệ, rộng tối thiểu 300px. Tổng ảnh 664400 bytes.
- Cloud checkout cô lập: sao lưu catalogue trước thử, chọn SP8xx/SP9xx chưa tồn tại, tạo bằng WATCH rồi dùng giỏ codex_smoke_real_UUID. Không đưa sản phẩm thử vào index. Thêm/cập nhật giỏ giữ stock=5, xác nhận mua 3 giảm còn 2, đơn/tổng tiền đúng; gửi lại cùng mã không trừ thêm. Dọn đúng 5 key do bài thử sở hữu: Hash sản phẩm, giỏ (đã xóa khi thành công), đơn, items, mã idempotency. Stock cả 20 sản phẩm catalogue không thay đổi.
- UI trên Cloud: 20 sản phẩm, 5 bộ lọc mỗi loại 4; trang Galaxy A16 hiển thị RAM/bộ nhớ/màn hình/5G, giá 4.990.000 đồng, link Samsung. Thêm 2 vào giỏ riêng cho tổng 9.980.000 đồng, không đổi stock. Giỏ riêng được dọn qua API giao diện, không thao tác giỏ người dùng.
- 375/768/1024/1440px: 20 card, không tràn ngang, không ảnh lỗi trong ảnh đã tải; console warning/error: 0. HTTP riêng đã xác minh đủ cả 20 ảnh, kể cả ảnh lazy-load ngoài màn hình.

## Quan sát Another Redis Desktop Manager

```redis
HGETALL product:SP001
HGETALL product:SP010
HGETALL product:SP020
SCARD products:all
SMEMBERS products:category:dien-thoai
SMEMBERS products:category:phu-kien
HGET product:SP001 stock
```

Hash có specs JSON và image local; không binary/base64. Giữ chính sách tồn kho/TTL của checkout đã có.

## Bảo mật và giới hạn

.env.example đã chứa giá trị kết nối thật tại thời điểm kiểm tra. Đã thay bằng mẫu trống mà không hiển thị bí mật; .env không bị chỉnh sửa. Không tìm thấy file mẫu được Git track hoặc trong git log --all của checkout này. Nếu bạn từng gửi file/bundle chứa mật khẩu ra ngoài lịch sử Git này, hãy đổi credential đó. Không commit/push trong nhiệm vụ.

Giá là giá minh họa từ JSON, không xác minh giá bán hiện hành. Ảnh có thể chứa nhiều biến thể màu cùng model; cấu hình laptop phụ thuộc SKU. Quyền ảnh của hãng/nhà bán lẻ chưa được cấp cho sử dụng thương mại; hiện dùng nội bộ học thuật. Không tuyên bố có giấy phép thương mại.

Backup không phải công cụ rollback tự động; nếu cần khôi phục metadata hãy review bản sao lưu và giữ stock hiện tại, không ghi stock trong backup lên hệ thống đang chạy. Redis transaction không rollback lỗi tài nguyên lúc EXEC; các kiểu key được kiểm tra trước khi ghi và xung đột WATCH được retry.
