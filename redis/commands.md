# Kiểm tra trong Another Redis Desktop Manager

Sau khi seed, refresh database 0. Dùng bộ lọc product:* để xem 20 Hash; products:* để xem 1 Set toàn bộ và 5 Set danh mục; cart:* để xem giỏ. Giỏ mẫu sẽ tự hết hạn sau 1800 giây. HLEN là số loại sản phẩm, tổng số lượng phải cộng các value.

Các lệnh đọc:
```redis
PING
HGETALL product:SP001
SCARD products:all
SMEMBERS products:all
SMEMBERS products:category:dien-thoai
HGETALL cart:demo
HLEN cart:demo
TTL cart:demo
```

Các lệnh minh họa ghi, chỉ chạy khi chủ động demo trên cart:manual:
```redis
HSET cart:manual SP001 2 SP005 1
HINCRBY cart:manual SP001 1
HGETALL cart:manual
EXPIRE cart:manual 1800
TTL cart:manual
HDEL cart:manual SP005
DEL cart:manual
```

HSET thêm/đặt số lượng; HINCRBY cộng số lượng; HGETALL đọc giỏ; HDEL xóa field; EXPIRE đặt hạn; TTL xem hạn (-1 không hạn, -2 không tồn tại); DEL xóa key. Các lệnh thủ công không tự áp dụng kiểm tra 0–99 của API. Không dùng FLUSHDB/FLUSHALL.
