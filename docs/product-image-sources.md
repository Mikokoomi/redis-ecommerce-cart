# Nguồn ảnh sản phẩm RedisCart

Ảnh được tải từ URL trong JSON hoặc ảnh thay thế trên trang sản phẩm của hãng. Chỉ dùng nội bộ cho đồ án học thuật; chưa xác minh hoặc tuyên bố giấy phép sử dụng thương mại. Cần xin quyền trước khi phát hành công khai.

Giá trong products_real_20.json là giá minh họa, không phải báo giá bán lẻ hiện tại đã xác minh. Màu ảnh là biến thể cùng model; RAM/SSD laptop tùy SKU như dữ liệu đầu vào, không suy ra từ ảnh.

20 ảnh đều có response thành công, Content-Type image/*, giải mã Pillow thành công và được lưu WebP. Redis chỉ chứa metadata/path. Tất cả ảnh đầu ra rộng ít nhất 300px, tối đa 1000px; giữ tỷ lệ. SP019 cắt khoảng trắng quanh sản phẩm theo crop ghi trong manifest. Không có ảnh SVG dựng thay cho sản phẩm thật.

| Mã | Sản phẩm | Nguồn trang | File ảnh gốc | Ảnh local | Kích thước | Dung lượng |
| --- | --- | --- | --- | --- | --- | --- |
| SP001 | Samsung Galaxy A16 5G 8GB/128GB | [Nguồn](https://cuahangsamsung.vn/shop/product/samsung-galaxy-a16-5g-8gb-128gb) | [Ảnh](https://cuahangsamsung.vn/filemanager/userfiles/hinh-san-pham/a16/5g/1.jpg) | /assets/images/products/SP001.webp | 1000×1000 | 41,480 bytes |
| SP002 | Xiaomi Redmi Note 13 8GB/128GB | [Nguồn](https://www.mi.com/vn/product/redmi-note-13/specs/) | [Ảnh](https://i02.appmifile.com/201_operator_sg/11/01/2024/64678266600f8b06f6e6217efa095556.png) | /assets/images/products/SP002.webp | 1000×500 | 25,062 bytes |
| SP003 | OPPO A60 8GB/256GB | [Nguồn](https://www.sulpak.kz/g/smartfoniy-oppo-a60-8256gb-ripple-blue/tekeli) | [Ảnh](https://object.pscloud.io/cms/cms/Photo/img_0_77_6016_0_6_RLPyFQ.png) | /assets/images/products/SP003.webp | 512×512 | 18,172 bytes |
| SP004 | Apple iPhone 15 128GB | [Nguồn](https://mediamart.vn/apple-iphone-15-128gb-hong) | [Ảnh](https://cdn.mediamart.vn/images/product/apple-iphone-15-128gb-hong_34e6a626.png) | /assets/images/products/SP004.webp | 600×600 | 18,256 bytes |
| SP005 | Lenovo IdeaPad Slim 3 15IRH8 | [Nguồn](https://donicelectronics.com/) | [Ảnh](https://donicelectronics.com/cdn/shop/files/IdeaPad_Slim_3_15IRH8_CT1_04.jpg?v=1762410711) | /assets/images/products/SP005.webp | 1000×1000 | 30,494 bytes |
| SP006 | ASUS Vivobook 15 X1504 | [Nguồn](https://www.asus.com/tw/laptops/for-home/vivobook/asus-vivobook-15-x1504/shop/) | [Ảnh](https://dlcdnwebimgs.asus.com/gain/0dea7490-edcd-4bfb-80e4-0324085f46fc/) | /assets/images/products/SP006.webp | 1000×1000 | 22,902 bytes |
| SP007 | Acer Aspire 5 A515-58P-51M3 | [Nguồn](https://store.acer.com/en-us/aspire-5-laptop-a515-58p-51m3) | [Ảnh](https://static-ecpa.acer.com/media/catalog/product/a/c/acer-aspire-5-a515-58p-non-fingerprint-non-backlit-wallpaper-steel-gray-01-1000x1000_nx.khjaa.001.png) | /assets/images/products/SP007.webp | 1000×1000 | 50,652 bytes |
| SP008 | Dell Inspiron 15 3530 | [Nguồn](https://vpem.vn/laptop-dell-inspiron-15-3530-i3-1305u-ram-8gb-512gb-ssd-120hz-windows-11-office-n3530-i3u085w11blu-.html) | [Ảnh](https://vpem.vn/uploads/2176/images/z4479561083771_b5f25e00d8ef8e3878a23a0001fbda31.jpg) | /assets/images/products/SP008.webp | 1000×663 | 67,842 bytes |
| SP009 | JBL Tune 520BT | [Nguồn](https://shop.ncsu.edu/JBL-Tune-520BT-Wireless-On-Ear-Headphones) | [Ảnh](https://shop.ncsu.edu/Product%20Images/JBL520Wireless_media-01.jpg) | /assets/images/products/SP009.webp | 1000×1000 | 41,124 bytes |
| SP010 | Sony WH-CH520 | [Nguồn](https://store.sony.com.au/headphones-bluetooth/WHCH520L.html) | [Ảnh](https://store.sony.com.au/on/demandware.static/-/Sites-sony-master-catalog/default/dwc5323103/images/WHCH520L/WHCH520L.png) | /assets/images/products/SP010.webp | 1000×1000 | 21,740 bytes |
| SP011 | Soundcore Q20i | [Nguồn](https://www.soundcore.com/vn/products/q20i-a3004z11) | [Ảnh](https://cdn.shopify.com/s/files/1/0609/8154/3047/files/A3004Z11_TD01_V1_3840x.jpg?v=1721705058) | /assets/images/products/SP011.webp | 1000×1000 | 39,262 bytes |
| SP012 | Apple AirPods (thế hệ 3) | [Nguồn](https://www.tadbuy.com/audifonos/5797-apple-airpods-3-3a-generacion-con-caja-de-carga-magsafe-1-audifonos-apple-7502079970916.html) | [Ảnh](https://www.tadbuy.com/27647/apple-airpods-3-3a-generacion-con-caja-de-carga-magsafe-1-audifonos-apple.jpg) | /assets/images/products/SP012.webp | 1000×1000 | 18,560 bytes |
| SP013 | Samsung Galaxy Watch6 Bluetooth 40mm | [Nguồn](https://shop.samsung.com/tr/galaxy-watch6-bluetooth-40mm/) | [Ảnh](https://samsung-akinon.a-cdn.akinoncdn.com/products/2023/07/21/18230/f0519b3e-da2f-49bd-9de7-c202ee000287.jpg) | /assets/images/products/SP013.webp | 1000×1000 | 32,976 bytes |
| SP014 | Apple Watch SE (thế hệ 2) GPS 40mm | [Nguồn](https://rauvang.com/chi-tiet/1111-apple-watch-se-gen-2-gps-40mm-starlight-aluminum-case-with-sport-band.htm) | [Ảnh](https://rauvang.com/data/Product/mplq3ref-vw-34frwatch-40-alum-starlight-nc-se-vw-34fr-wf-co.htm_1663384417.jpeg) | /assets/images/products/SP014.webp | 1000×1000 | 36,888 bytes |
| SP015 | Xiaomi Redmi Watch 4 | [Nguồn](https://www.photopoint.ee/en/sports-watches/4401178-xiaomi-redmi-watch-4-obsidian-black) | [Ảnh](https://static1.nordic.pictures/45869497-thickbox_default/xiaomi-redmi-watch-4-obsidian-black.jpg) | /assets/images/products/SP015.webp | 800×800 | 36,210 bytes |
| SP016 | HUAWEI WATCH FIT 3 | [Nguồn](https://ennap.com/ar/products/huawei-watch-fit-3) | [Ảnh](https://ennap.com/cdn/shop/files/800_800_44337A32F7D691E83D5B0E62D0777C07mp.png?v=1718822874&width=1946) | /assets/images/products/SP016.webp | 800×800 | 39,854 bytes |
| SP017 | Logitech M331 Silent Plus | [Nguồn](https://www.logitech.com/vi-vn/shop/p/m331-silent-plus-mouse.910-004914) | [Ảnh](https://resource.logitech.com/w_1000,h_1000,c_pad,q_auto,f_auto/d_transparent.gif/content/dam/logitech/en/products/mice/m330-wireless-silent-mouse/2024-update/gallery/m330-wireless-mouse-top-view-black-gallery-01.png) | /assets/images/products/SP017.webp | 1000×1000 | 21,348 bytes |
| SP018 | Logitech Pebble Keys 2 K380s | [Nguồn](https://www.logitech.com/en-us/shop/o/keyboard-gifts) | [Ảnh](https://resource.logitech.com/e_trim/w_700%2Ch_600%2Cc_pad%2Cq_auto%2Cf_auto%2Cdpr_1.0/b_white/content/dam/logitech/en/products/keyboards/pebble-keys-2-k380s/gallery/pebble-keys-2-k380s-top-tonal-graphite-gallery-us.png) | /assets/images/products/SP018.webp | 700×600 | 25,060 bytes |
| SP019 | Anker 323 Charger 33W | [Nguồn](https://www.anker.com/vn/products/a2331) | [Ảnh](https://cdn.shopify.com/s/files/1/0614/8109/1153/files/A2331111_TD_01.png?v=1720583092&width=1600) | /assets/images/products/SP019.webp | 1000×876 | 26,318 bytes |
| SP020 | UGREEN Revodok 105 5-in-1 USB-C Hub | [Nguồn](https://www.ugreen.com/products/usa-15495) | [Ảnh](https://www.ugreen.com/cdn/shop/files/d0a9824bf408d4d39de70224bbafb22d.png?v=1762322082&width=1000) | /assets/images/products/SP020.webp | 1000×1000 | 50,200 bytes |

## Thay thế và đối chiếu

- SP002: Nguồn JSON không phân giải DNS; thay bằng ảnh trên trang chính hãng.
- SP011: Nguồn JSON trả 403; thay bằng ảnh Q20i của hãng.
- SP017: Dùng ảnh gallery do trang hãng M331 cung cấp thay nguồn bên thứ ba.
- SP019: Nguồn JSON trả 403; thay bằng ảnh Anker 323 của hãng.
- SP020: Thay ảnh marketing bằng ảnh sản phẩm chính trên cùng trang hãng.

SP002 đã thử ảnh swatch từ trang hãng nhưng ảnh dưới 300px nên bị loại; ảnh cuối cùng là ảnh chính của trang thông số. Một số model có ảnh nhiều màu cùng lúc (Redmi Note 13, JBL Tune 520BT). Đã xem bảng contact sheet và ảnh trên web để đối chiếu model. SP017 dùng asset M330/M331 do chính trang M331 của Logitech liên kết.

Manifest docs/product-image-manifest.json giữ URL thực tế sau redirect, kích thước nguồn/đầu ra, MIME, SHA-256, dung lượng và crop để tái kiểm tra.
