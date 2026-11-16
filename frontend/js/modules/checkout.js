
import {
  $, state, api, esc, money, empty, message
} from './core.js';

import {
  authReady, requireLogin, cartPath
} from './auth-state.js';

import { loadCart } from './cart.js';
import { loadProducts } from './products.js';

const storageKey = userId =>
  'rediscart.checkout.' + userId;

function readPending(userId) {
  try {
    return localStorage.getItem(storageKey(userId)) || '';
  } catch {
    return state.checkoutKey;
  }
}

function clearPending(userId) {
  state.checkoutKey = '';

  try {
    localStorage.removeItem(storageKey(userId));
  } catch {}
}

const buyNowStorageKey = userId =>
  'rediscart.buy-now.' + userId;

function readBuyNow(userId) {
  try {
    const raw = sessionStorage.getItem(
      buyNowStorageKey(userId)
    );

    if (!raw) return null;

    const intent = JSON.parse(raw);

    if (
      !/^SP[0-9]{3}$/.test(intent.product_id) ||
      !Number.isInteger(intent.quantity) ||
      intent.quantity < 1 ||
      intent.quantity > 99 ||
      typeof intent.request_key !== 'string' ||
      !/^[a-zA-Z0-9_-]{8,128}$/.test(intent.request_key)
    ) {
      return null;
    }

    return intent;
  } catch {
    return null;
  }
}

function clearBuyNow(userId) {
  try {
    sessionStorage.removeItem(buyNowStorageKey(userId));
  } catch {}
}
// Hien thi danh sach san pham trong don
function orderLines(items) {
  return items.map(item => `
    <div class="review-item">
      <div>
        <strong>
          ${esc(item.product_name || item.name)}
        </strong>

        <p>
          ${item.quantity} ×
          ${money(item.unit_price_vnd ?? item.price_vnd)}
        </p>
      </div>

      <strong>
        ${money(item.subtotal_vnd)}
      </strong>
    </div>
  `).join('');
}

// Chuan bi trang xac nhan mua

export async function prepareCheckout() {
  await authReady;

  if (!state.user) {
    location.hash = 'catalog';
    requireLogin();
    return;
  }

  const userId = state.user.user_id;
  const intent = readBuyNow(userId);
  const confirmButton = $('#checkout-confirm');

  confirmButton.disabled = true;
  $('#checkout-review').textContent =
    'Đang tải thông tin mua hàng…';

  try {
    if (intent) {
      const p = await api(
        '/products/' + encodeURIComponent(intent.product_id)
      );

      if (
        state.user?.user_id !== userId ||
        location.hash !== '#checkout'
      ) return;

      const stock = Number(p.stock);
      const price = Number(p.price_vnd);

      const valid =
        Number.isInteger(stock) &&
        Number.isSafeInteger(price) &&
        price >= 0 &&
        stock >= intent.quantity;

      const item = {
        product_name: p.name,
        quantity: intent.quantity,
        unit_price_vnd: price,
        subtotal_vnd: price * intent.quantity
      };

      $('#checkout-review').innerHTML =
        orderLines([item]) +
        `
          <div class="review-total">
            Tổng tiền
            <strong>${money(item.subtotal_vnd)}</strong>
          </div>
          <p class="checkout-notice">
            Mua ngay: chỉ xác nhận sản phẩm này.
            Giỏ hàng hiện tại không bị thay đổi.
          </p>
        `;

      confirmButton.textContent = 'Xác nhận mua ngay';
      confirmButton.disabled = !valid;

      if (!valid) {
        message(
          'Sản phẩm không đủ tồn kho hoặc giá không hợp lệ.',
          true
        );
      }

      return;
    }

    // Thanh toan gio hang nhu cu.
    state.checkoutKey = readPending(userId);

    const cart = await api(cartPath());

    if (
      state.user?.user_id !== userId ||
      location.hash !== '#checkout'
    ) return;

    $('#checkout-review').innerHTML =
      cart.items.length
        ? orderLines(cart.items) +
          `
            <div class="review-total">
              Tổng tiền
              <strong>${money(cart.total_vnd)}</strong>
            </div>
          `
        : empty(
            'Giỏ hàng đang trống',
            state.checkoutKey
              ? 'Có yêu cầu chưa rõ kết quả. Chọn kiểm tra lại bên dưới.'
              : 'Quay lại mua sắm để thêm sản phẩm.'
          );

    confirmButton.textContent =
      state.checkoutKey
        ? 'Kiểm tra lại yêu cầu đã gửi'
        : 'Xác nhận mua hàng';

    confirmButton.disabled =
      !cart.items.length && !state.checkoutKey;

  } catch (error) {
    if (state.user?.user_id === userId) {
      message(error.message, true);
    }
  }
}


// Hien thi chi tiet don hang
export async function loadOrder(orderId) {
  await authReady;

  if (!state.user) {
    location.hash = 'catalog';
    requireLogin();
    return;
  }

  const userId = state.user.user_id;

  $('#order-content').textContent =
    'Đang tải đơn hàng…';

  try {
    const order = await api(
      cartPath() +
      '/orders/' +
      encodeURIComponent(orderId)
    );

    if (
      state.user?.user_id !== userId ||
      !location.hash.startsWith('#order/')
    ) return;

    $('#order-content').innerHTML = `
      <div class="success-mark" aria-hidden="true">✓</div>

      <h1>Xác nhận mua hàng thành công</h1>

      <p class="checkout-notice">
        Đơn hàng đã được xác nhận.
        Không thu tiền trực tuyến.
      </p>

      <dl class="order-meta">
        <div>
          <dt>Mã đơn hàng</dt>
          <dd>${esc(order.order_id)}</dd>
        </div>

        <div>
          <dt>Thời gian xác nhận</dt>
          <dd>
            ${esc(
              new Date(order.created_at)
                .toLocaleString('vi-VN')
            )}
          </dd>
        </div>

        <div>
          <dt>Trạng thái</dt>
          <dd>Đã xác nhận</dd>
        </div>
      </dl>

      ${orderLines(order.items)}

      <div class="review-total">
        Tổng tiền
        <strong>${money(order.total_vnd)}</strong>
      </div>

      <a href="#catalog" class="button primary">
        Quay lại mua sắm
      </a>
    `;

  } catch (error) {
    if (state.user?.user_id === userId) {
      $('#order-content').innerHTML = empty(
        'Không tải được đơn hàng',
        error.message
      );
    }
  }
}

// Su kien xac nhan mua hang

export function bindCheckout() {
  $('#checkout-open').onclick = () => {
    // Khi thanh toan tu gio hang, huy lua chon Mua ngay.
    if (state.user) {
      clearBuyNow(state.user.user_id);
    }

    if (location.hash === '#checkout') {
      prepareCheckout();
    } else {
      location.hash = 'checkout';
    }
  };

  $('#checkout-confirm').onclick = async () => {
    await authReady;

    if (!state.user) {
      requireLogin();
      return;
    }

    if (state.checkoutBusy) return;

    const userId = state.user.user_id;
    const intent = readBuyNow(userId);

    state.checkoutBusy = true;
    $('#checkout-confirm').disabled = true;

    try {
      let result;

      if (intent) {
        // MUA NGAY: khong lay san pham trong gio.
        result = await api(
          '/cart/' + encodeURIComponent(userId) + '/buy-now',
          {
            method: 'POST',
            body: JSON.stringify({
              confirmed: true,
              idempotency_key: intent.request_key,
              product_id: intent.product_id,
              quantity: intent.quantity
            })
          }
        );
      } else {
        // THANH TOAN GIO: giu nguyen luong cu.
        if (!state.checkoutKey) {
          state.checkoutKey = crypto.randomUUID();

          try {
            localStorage.setItem(
              storageKey(userId),
              state.checkoutKey
            );
          } catch {
            throw Error(
              'Không lưu được mã giao dịch. Hãy bật lưu trữ trình duyệt rồi thử lại.'
            );
          }
        }

        result = await api(
          '/cart/' + encodeURIComponent(userId) + '/checkout',
          {
            method: 'POST',
            body: JSON.stringify({
              confirmed: true,
              idempotency_key: state.checkoutKey
            })
          }
        );
      }

      if (state.user?.user_id !== userId) return;

      if (intent) {
        clearBuyNow(userId);
      } else {
        clearPending(userId);
      }

      location.hash = 'order/' + result.order_id;

      loadCart();
      loadProducts();

    } catch (error) {
      if (state.user?.user_id === userId) {
        message(
          error.message +
          ' Nếu chưa rõ kết quả, hãy thử lại cùng yêu cầu.',
          true
        );
      }
    } finally {
      if (state.user?.user_id === userId) {
        state.checkoutBusy = false;
        $('#checkout-confirm').disabled = false;
      }
    }
  };
}
