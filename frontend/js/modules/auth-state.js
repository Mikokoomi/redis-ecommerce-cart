
import { $, state, message } from './core.js';

export const authReady = fetch('/api/auth/me', {
  credentials: 'same-origin'
})
  .then(async response =>
    response.ok ? response.json() : null
  )
  .then(user => {
    if (state.authVersion === 0) {
      state.user = user;
    }
  })
  .catch(() => {});

export const cartPath = () =>
  '/cart/' + encodeURIComponent(state.user.user_id);

// Chua dang nhap thi mo form dang nhap
export function requireLogin() {
  message(
    'Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng.',
    true
  );

  window.dispatchEvent(
    new Event('rediscart:open-login')
  );
}

// Lang nghe khi dang nhap / dang xuat
export function bindAuth(onChange) {
  window.addEventListener(
    'rediscart:auth-changed',
    event => {
      state.authVersion++;
      state.cartRequest++;
      state.mutationId++;

      state.user = event.detail?.user_id
        ? event.detail
        : null;

      state.cart = null;
      state.busy = false;
      state.checkoutKey = '';
      state.checkoutBusy = false;

      // Xoa du lieu tai khoan cu ngay lap tuc
      $('#count').textContent = '0';

      $('.cart-link').setAttribute(
        'aria-label',
        'Giỏ hàng, 0 sản phẩm'
      );

      $('#cart-items').textContent = '';
      $('#summary-quantity').textContent = '0';
      $('#subtotal').textContent = '0 ₫';
      $('#total').textContent = '0 ₫';
      $('#checkout-open').disabled = true;
      $('#checkout-review').textContent = '';
      $('#order-content').textContent = '';
      $('#cart-description').textContent = '';
      $('#clear-dialog').close();

      if (state.user) message('');

      if (
        location.hash === '#checkout' ||
        location.hash.startsWith('#order/')
      ) {
        location.hash = 'catalog';
      }

      onChange();
    }
  );
}
