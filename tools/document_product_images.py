"""Sinh bảng nguồn ảnh từ manifest đã kiểm tra."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
manifest=json.loads((ROOT/"docs/product-image-manifest.json").read_text(encoding="utf-8"))
overrides=json.loads((ROOT/"tools/product-image-overrides.json").read_text(encoding="utf-8"))
lines=[
"# Nguồn ảnh sản phẩm RedisCart",
"",
"Ảnh được tải từ URL trong JSON hoặc ảnh thay thế trên trang sản phẩm của hãng. Chỉ dùng nội bộ cho đồ án học thuật; chưa xác minh hoặc tuyên bố giấy phép sử dụng thương mại. Cần xin quyền trước khi phát hành công khai.",
"",
"Giá trong products_real_20.json là giá minh họa, không phải báo giá bán lẻ hiện tại đã xác minh. Màu ảnh là biến thể cùng model; RAM/SSD laptop tùy SKU như dữ liệu đầu vào, không suy ra từ ảnh.",
"",
"20 ảnh đều có response thành công, Content-Type image/*, giải mã Pillow thành công và được lưu WebP. Redis chỉ chứa metadata/path. Tất cả ảnh đầu ra rộng ít nhất 300px, tối đa 1000px; giữ tỷ lệ. SP019 cắt khoảng trắng quanh sản phẩm theo crop ghi trong manifest. Không có ảnh SVG dựng thay cho sản phẩm thật.",
"",
"| Mã | Sản phẩm | Nguồn trang | File ảnh gốc | Ảnh local | Kích thước | Dung lượng |",
"| --- | --- | --- | --- | --- | --- | --- |",
]
for pid,p in sorted(manifest.items()):
    assert p["status"]=="ok"
    lines.append(f'| {pid} | {p["name"]} | [Nguồn]({p["source_page"]}) | [Ảnh]({p["url"]}) | {p["local"]} | {p["size"][0]}×{p["size"][1]} | {p["bytes"]:,} bytes |')
lines.extend(["","## Thay thế và đối chiếu",""])
for pid,item in sorted(overrides.items()):
    lines.append(f'- {pid}: {item["reason"]}')
lines.extend(["","SP002 đã thử ảnh swatch từ trang hãng nhưng ảnh dưới 300px nên bị loại; ảnh cuối cùng là ảnh chính của trang thông số. Một số model có ảnh nhiều màu cùng lúc (Redmi Note 13, JBL Tune 520BT). Đã xem bảng contact sheet và ảnh trên web để đối chiếu model. SP017 dùng asset M330/M331 do chính trang M331 của Logitech liên kết.","","Manifest docs/product-image-manifest.json giữ URL thực tế sau redirect, kích thước nguồn/đầu ra, MIME, SHA-256, dung lượng và crop để tái kiểm tra.",""])
(ROOT/"docs/product-image-sources.md").write_text("\n".join(lines),encoding="utf-8")
print("DOCUMENTED_IMAGES",len(manifest))
print("TOTAL_IMAGE_BYTES",sum(p["bytes"] for p in manifest.values()))

