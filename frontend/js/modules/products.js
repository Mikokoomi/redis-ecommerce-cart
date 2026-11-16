
import {
  $, state, api, categories, money, esc,
  image, plusIcon, empty, setupImages, message
} from './core.js';

import { mutate } from './cart.js';
import {
  authReady, requireLogin
} from './auth-state.js';
const normalize = value =>
  String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .toLowerCase();

// =============================
// DANH SACH SAN PHAM
// =============================

export async function loadProducts() {
  const request = ++state.productRequest;

  $('#products').setAttribute('aria-busy', 'true');

  $('#products').innerHTML = Array(4)
    .fill('<div class="skeleton" aria-hidden="true"></div>')
    .join('');

  $('#result-count').textContent = 'Đang tải…';

  try {
    const data = await api(
      '/products' +
      (state.selected
        ? '?category=' + encodeURIComponent(state.selected)
        : '')
    );

    if (request !== state.productRequest) return;

    const found = data.filter(p =>
      normalize(p.name + ' ' + (p.description || ''))
        .includes(normalize(state.query))
    );

    $('#catalog-title').textContent = state.query
      ? 'Kết quả tìm kiếm'
      : (categories[state.selected] || 'Tất cả') +
        (state.selected ? '' : ' sản phẩm');

    $('#result-count').textContent =
      `${found.length} sản phẩm`;

    $('#products').innerHTML = found.length
      ? found.map(p => `
          <article class="product">
            <a
              class="product-image"
              href="#product/${encodeURIComponent(p.product_id)}">

              <img
                src="${image(p)}"
                width="320"
                height="240"
                alt="${esc(p.name)}"
                loading="lazy">
            </a>

            <div class="product-body">

              <small>
                ${esc(categories[p.category] || p.category)}
              </small>

              <h3>
                <a href="#product/${encodeURIComponent(p.product_id)}">
                  ${esc(p.name)}
                </a>
              </h3>

              <p class="price">
                ${money(p.price_vnd)}
              </p>

              <span class="stock ${p.stock <= 0 ? 'out' : ''}">
                ${
                  p.stock > 0
                    ? `Còn ${p.stock} sản phẩm`
                    : 'Hết hàng'
                }
              </span>

              <button
                class="add-button"
                data-add="${esc(p.product_id)}"
                data-unavailable="${p.stock <= 0}"
                ${state.busy || p.stock <= 0 ? 'disabled' : ''}
                aria-label="Thêm ${esc(p.name)} vào giỏ">

                ${plusIcon}
                ${p.stock <= 0 ? 'Hết hàng' : 'Thêm vào giỏ'}
              </button>

            </div>
          </article>
        `).join('')
      : empty(
          'Chưa tìm thấy sản phẩm',
          'Thử từ khóa khác hoặc chọn danh mục phù hợp.'
        );

    setupImages($('#products'));

  } catch (error) {
    if (request !== state.productRequest) return;

    $('#products').innerHTML = empty(
      'Không tải được sản phẩm',
      'Kiểm tra kết nối và chọn Tải lại để thử lần nữa.'
    );

    $('#result-count').textContent = '';
    message(error.message, true);

  } finally {
    if (request === state.productRequest) {
      $('#products').setAttribute('aria-busy', 'false');
    }
  }
}

// =============================
// LOC VA TIM KIEM SAN PHAM
// =============================

export function bindCatalog() {
  $('#filters').innerHTML = Object.entries(categories)
    .map(([key, label]) => `
      <button
        data-category="${key}"
        aria-pressed="${!key}"
        class="${key ? '' : 'active'}">
        ${label}
      </button>
    `).join('');

  $('#filters').onclick = event => {
    const button = event.target.closest('[data-category]');

    if (!button) return;

    state.selected = button.dataset.category;

    $('#filters')
      .querySelectorAll('button')
      .forEach(item => {
        item.classList.toggle(
          'active',
          item === button
        );

        item.setAttribute(
          'aria-pressed',
          String(item === button)
        );
      });

    loadProducts();
  };

  let searchTimer;

  $('#search').addEventListener('input', () => {
    clearTimeout(searchTimer);

    state.query = $('#search').value.trim();

    searchTimer = setTimeout(
      loadProducts,
      250
    );
  });

  $('#search-form').onsubmit = event => {
    event.preventDefault();

    clearTimeout(searchTimer);
    state.query = $('#search').value.trim();

    location.hash = 'catalog';
    loadProducts();
  };
}

// =============================
// THONG SO KY THUAT
// =============================

const specLabels = {
  screen: 'Màn hình',
  storage: 'Bộ nhớ',
  ram: 'RAM',
  connectivity: 'Kết nối',
  main_camera: 'Camera chính',
  battery: 'Pin',
  charging: 'Sạc',
  chip: 'Chip',
  screen_class: 'Kích thước màn hình',
  model_family: 'Dòng sản phẩm',
  usage: 'Nhu cầu',
  panel: 'Tấm nền',
  series: 'Dòng máy',
  sku: 'Mã SKU',
  connection: 'Kết nối',
  design: 'Thiết kế',
  noise_control: 'Chống ồn',
  type: 'Loại sản phẩm',
  case: 'Kích thước vỏ',
  generation: 'Thế hệ',
  body: 'Khung',
  weight: 'Khối lượng',
  water_resistance: 'Chống nước',
  feature: 'Tính năng',
  max_power: 'Công suất tối đa',
  ports: 'Số cổng',
  hdmi: 'HDMI'
};

function specifications(p) {
  const specs =
    p.specs && typeof p.specs === 'object'
      ? p.specs
      : {};

  const rows = Object.entries(specs)
    .map(([key, value]) => `
      <div>
        <dt>${esc(specLabels[key] || key)}</dt>
        <dd>${esc(value)}</dd>
      </div>
    `).join('');

  const source =
    /^https:\/\//.test(p.manufacturer_url || '')
      ? `
        <a
          class="manufacturer-link"
          target="_blank"
          rel="noopener noreferrer"
          href="${esc(p.manufacturer_url)}">

          Thông tin từ
          ${esc(p.brand || 'nhà sản xuất')} ↗
        </a>
      `
      : '';

  return (
    rows
      ? `
        <section class="specifications">
          <h2>Thông số sản phẩm</h2>
          <dl>${rows}</dl>
        </section>
      `
      : ''
  ) + source;
}


/* =========================================
   REDISCART - CHI TIET SAN PHAM MOI
   ========================================= */

export async function loadDetail(productId) {
  const request = ++state.detailRequest;
  const root = $('#detail-content');

  root.innerHTML = `
    <div class="rd-loading">
      Đang tải thông tin sản phẩm...
    </div>
  `;

  try {
    const p = await api(
      '/products/' + encodeURIComponent(productId)
    );

    if (request !== state.detailRequest) return;

    const stock = Math.max(
      0,
      Math.trunc(Number(p.stock) || 0)
    );

    const maxQuantity = Math.min(
      99,
      Math.max(1, stock)
    );

    const inStock = stock > 0;

    const description = (
      p.description || ''
    )
      .replace(/\s*Dữ liệu mẫu đồ án\.?/gi, '')
      .trim();

    const categoryName =
      categories[p.category] || p.category || 'Sản phẩm';

    const technicalInfo = specifications(p);

    // Giam gia: chi hien khi co gia goc hop le
    const sellingPrice = Number(p.price_vnd);
    const originalPrice = Number(
      p.original_price_vnd ?? NaN
    );

    const hasSale =
      Number.isFinite(sellingPrice) &&
      Number.isFinite(originalPrice) &&
      sellingPrice > 0 &&
      originalPrice > sellingPrice;

    const discountPercent = hasSale
      ? Math.round(
          (1 - sellingPrice / originalPrice) * 100
        )
      : 0;

    const savingAmount = hasSale
      ? originalPrice - sellingPrice
      : 0;

    // Hien thi toi da 3 thong so noi bat
    const quickSpecs = Object.entries(
      p.specs && typeof p.specs === 'object'
        ? p.specs
        : {}
    )
      .filter(([, value]) =>
        value !== null &&
        value !== '' &&
        typeof value !== 'object'
      )
      .slice(0, 3)
      .map(([key, value]) => `
        <div class="rd-quick-spec">
          <span>${esc(specLabels[key] || key)}</span>
          <strong>${esc(value)}</strong>
        </div>
      `)
      .join('');

    root.innerHTML = `
      <div class="rd-product">

        <!-- Duong dan -->
        <nav class="rd-breadcrumb"
             aria-label="Đường dẫn trang">

          <a href="#catalog">Trang chủ</a>
          <span aria-hidden="true">/</span>

          <a href="#categories">
            ${esc(categoryName)}
          </a>

          <span aria-hidden="true">/</span>

          <span aria-current="page">
            ${esc(p.name)}
          </span>

        </nav>

        <!-- Khu vuc san pham chinh -->
        <div class="rd-product-main">

          <!-- Anh san pham -->
          <section class="rd-product-media"
                   aria-label="Hình ảnh sản phẩm">

            
        <div class="rd-product-photo">

        ${hasSale ? `
            <span class="rd-photo-sale">
            GIẢM ${discountPercent}%
            </span>
        ` : ''}

        <img
            src="${image(p)}"
            alt="${esc(p.name)}"
            loading="eager">
        </div>

          </section>

          <!-- Gia va mua hang -->
          <section class="rd-product-purchase">

            <p class="rd-product-category">
              ${esc(categoryName)}
            </p>

            <h1 class="rd-product-name">
              ${esc(p.name)}
            </h1>

            <div class="rd-product-meta">
              <span>Mã sản phẩm: ${esc(p.product_id)}</span>

              <span class="rd-stock ${inStock ? 'is-available' : 'is-empty'}">
                <span class="rd-stock-dot"></span>
                ${inStock ? `Còn ${stock} sản phẩm` : 'Hết hàng'}
              </span>
            </div>

            
        <div class="rd-price-box">

        <div class="rd-price-heading">
            <span class="rd-price-label">Giá bán tại RedisCart</span>

            ${hasSale ? `
            <span class="rd-discount-badge">
                Giảm ${discountPercent}%
            </span>
            ` : ''}
        </div>

  <div class="rd-price-amount">

    <strong class="rd-price-value">
      ${money(p.price_vnd)}
    </strong>

    ${hasSale ? `
      <del class="rd-original-price">
        ${money(originalPrice)}
      </del>
    ` : ''}

  </div>

        ${hasSale ? `
            <p class="rd-saving-note">
            Bạn tiết kiệm ${money(savingAmount)}
            so với giá gốc.
            </p>
        ` : ''}

        </div>

        ${quickSpecs ? `
        <div class="rd-quick-specs">
            ${quickSpecs}
        </div>
        ` : ''}


            <form id="detail-form"
                  class="rd-purchase-form">

              <label
                class="rd-quantity-label"
                for="detail-quantity">
                Số lượng
              </label>

              <div class="rd-purchase-row">

                <div class="rd-quantity">

                  <button
                    type="button"
                    data-qty-step="-1"
                    aria-label="Giảm số lượng"
                    ${!inStock ? 'disabled' : ''}>
                    −
                  </button>

                  <input
                    id="detail-quantity"
                    type="number"
                    inputmode="numeric"
                    min="1"
                    max="${maxQuantity}"
                    step="1"
                    value="1"
                    required
                    ${!inStock ? 'disabled' : ''}>

                  <button
                    type="button"
                    data-qty-step="1"
                    aria-label="Tăng số lượng"
                    ${!inStock ? 'disabled' : ''}>
                    +
                  </button>

                </div>

                
        <div class="rd-purchase-actions">

        <!-- Nút 1: Mua ngay -->
        <button
            type="submit"
            class="rd-buy-now"
            data-action="buy-now"
            ${!inStock ? 'disabled' : ''}>
            Mua ngay
        </button>

        <!-- Nút 2: Thêm giỏ hàng -->
        <button
            type="submit"
            class="rd-add-to-cart"
            data-action="add-to-cart"
            ${!inStock ? 'disabled' : ''}>

            <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 3h2l2.5 12h12L22 7H6"/>
            <circle cx="9" cy="20" r="1"/>
            <circle cx="18" cy="20" r="1"/>
            </svg>

            ${inStock ? 'Thêm vào giỏ' : 'Hết hàng'}

        </button>

        </div>

              </div>

            </form>

            <!-- Thong tin nghiep vu thuc -->
            <div class="rd-service-notes">

              <div>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 2 3 6v6c0 5.5 3.8 9 9 10 5.2-1 9-4.5 9-10V6Z"/>
                  <path d="m8 12 3 3 5-6"/>
                </svg>
                <span>
                  Tồn kho được kiểm tra khi xác nhận mua hàng
                </span>
              </div>

              <div>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="9"/>
                  <path d="M12 7v5l3 2"/>
                </svg>
                <span>
                  Giỏ hàng được lưu trong Redis trong 24 giờ
                </span>
              </div>

              <div>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="3" y="5" width="18" height="14" rx="2"/>
                  <path d="M3 10h18"/>
                </svg>
                <span>
                  Không thu tiền trực tuyến
                </span>
              </div>

            </div>

          </section>
        </div>

        <!-- Thong tin ben duoi -->
        <div class="rd-product-bottom">

          <section class="rd-description-card">
            <h2>Thông tin sản phẩm</h2>

            <p>
              ${
                description
                  ? esc(description)
                  : 'Thông tin mô tả đang được cập nhật.'
              }
            </p>
          </section>

          <div class="rd-specifications-card">
            ${
              technicalInfo ||
              '<section class="specifications"><h2>Thông số kỹ thuật</h2><p>Thông số đang được cập nhật.</p></section>'
            }
          </div>

        </div>

      </div>
    `;

    setupImages(root);

    // Nut tang/giam so luong
    const form = root.querySelector('#detail-form');
    const quantityInput = root.querySelector(
      '#detail-quantity'
    );

    form.querySelectorAll('[data-qty-step]')
      .forEach(button => {
        button.addEventListener('click', () => {
          const step = Number(
            button.dataset.qtyStep
          );

          const current =
            Number(quantityInput.value) || 1;

          quantityInput.value = Math.max(
            1,
            Math.min(maxQuantity, current + step)
          );
        });
      });

    // Them vao gio hang
    

form.addEventListener('submit', async event => {
  event.preventDefault();

  const quantity = Number(quantityInput.value);

  if (
    !Number.isInteger(quantity) ||
    quantity < 1 ||
    quantity > maxQuantity
  ) {
    message(
      `Vui lòng chọn số lượng từ 1 đến ${maxQuantity}.`,
      true
    );
    return;
  }

  const buyNow =
    event.submitter?.dataset.action === 'buy-now';

  const buttons = [
    ...form.querySelectorAll('button[type="submit"]')
  ];

  buttons.forEach(button => {
    button.disabled = true;
  });

  try {
    if (buyNow) {
      await authReady;

      if (!state.user) {
        requireLogin();
        return;
      }

      // Chi luu san pham duoc chon de xac nhan mua ngay.
      // Khong them vao gio hang Redis.
      sessionStorage.setItem(
        'rediscart.buy-now.' + state.user.user_id,
        JSON.stringify({
          product_id: p.product_id,
          quantity,
          request_key: crypto.randomUUID()
        })
      );

      location.hash = 'checkout';
      return;
    }

    // Nut Them vao gio van hoat dong nhu cu.
    await mutate('/items', 'POST', {
      product_id: p.product_id,
      quantity
    });

  } catch (error) {
    message(error.message, true);

  } finally {
    buttons.forEach(button => {
      button.disabled = !inStock;
    });
  }
});



  } catch (error) {
    if (request === state.detailRequest) {
      root.innerHTML = empty(
        'Không tải được thông tin sản phẩm',
        error.message
      );
    }
  }
}


