
import {
  $, state, api, money, esc, image,
  categories, setupImages, empty, message
} from './core.js';

import {
  authReady, requireLogin, cartPath
} from './auth-state.js';

// Khoa nut khi dang xu ly
export function setBusy(value) {
  state.busy = value;

  $('#cart-view').classList.toggle('busy', value);

  $('#cart-items').setAttribute(
    'aria-busy',
    String(value)
  );

  $('#checkout-open').disabled =
    value || !state.cart?.items?.length;

  document.querySelectorAll(
    '[data-add],[data-q],[data-remove],#clear'
  ).forEach(button => {
    button.disabled =
      value ||
      button.dataset.unavailable === 'true' ||
      button.dataset.limit === 'true' ||
      (
        button.id === 'clear' &&
        !state.cart?.items?.length
      );
  });
}

// Hien thi gio hang
export function renderCart(data) {
  state.cart = data;

  $('#count').textContent = data.total_quantity;

  $('.cart-link').setAttribute(
    'aria-label',
    `Giỏ hàng, ${data.total_quantity} sản phẩm`
  );

  $('#cart-description').textContent =
    `${data.items.length} loại sản phẩm`;

  $('#summary-quantity').textContent =
    data.total_quantity;

  $('#subtotal').textContent =
    money(data.total_vnd);

  $('#total').textContent =
    money(data.total_vnd);

  $('#cart-items').innerHTML = data.items.length
    ? data.items.map(p => `
        <article class="cart-item">

          <img
            src="${image(p)}"
            alt="${esc(p.name)}"
            width="96"
            height="104">

          <div>
            <small>
              ${esc(categories[p.category] || p.product_id)}
            </small>

            <h3>${esc(p.name)}</h3>

            <span class="unit-price">
              ${money(p.price_vnd)}
            </span>

            <div class="row">
              <div class="quantity">

                <button
                  data-id="${esc(p.product_id)}"
                  data-q="${p.quantity - 1}"
                  aria-label="Giảm số lượng">
                  −
                </button>

                <span aria-label="Số lượng">
                  ${p.quantity}
                </span>

                <button
                  data-id="${esc(p.product_id)}"
                  data-q="${p.quantity + 1}"
                  data-limit="${p.quantity >= 99}"
                  ${p.quantity >= 99 ? 'disabled' : ''}
                  aria-label="Tăng số lượng">
                  +
                </button>
              </div>

              <button
                class="remove"
                data-remove="${esc(p.product_id)}">
                Xóa
              </button>
            </div>
          </div>

          <strong class="line-total">
            ${money(p.subtotal_vnd)}
          </strong>
        </article>
      `).join('')
    : empty(
        'Giỏ hàng của bạn đang trống',
        'Khám phá sản phẩm và thêm lựa chọn phù hợp vào giỏ.'
      ) +
      `
        <a
          class="empty-shopping button secondary-button"
          href="#catalog">
          Khám phá sản phẩm →
        </a>
      `;

  setupImages($('#cart-items'));
  setBusy(state.busy);
}

// Tai gio rieng cua tai khoan dang nhap
export async function loadCart() {
  const request = ++state.cartRequest;

  await authReady;

  if (request !== state.cartRequest) return;

  const blank = {
    items: [],
    total_quantity: 0,
    total_vnd: 0,
    ttl: -2
  };

  renderCart(blank);

  if (!state.user) {
    $('#cart-items').innerHTML = empty(
      'Hãy đăng nhập để xem giỏ hàng',
      'Mỗi tài khoản có một giỏ hàng riêng.'
    );
    return;
  }

  const userId = state.user.user_id;

  $('#cart-items').textContent =
    'Đang tải giỏ hàng…';

  $('#cart-items').setAttribute(
    'aria-busy',
    'true'
  );

  try {
    const data = await api(cartPath());

    if (
      request !== state.cartRequest ||
      state.user?.user_id !== userId
    ) return;

    renderCart(data);

  } catch (error) {
    if (
      request !== state.cartRequest ||
      state.user?.user_id !== userId
    ) return;

    state.cart = null;

    $('#cart-items').innerHTML = empty(
      'Không tải được giỏ hàng',
      'Vui lòng thử lại.'
    );

    $('#clear').disabled = true;
    $('#checkout-open').disabled = true;

    message(error.message, true);

  } finally {
    if (request === state.cartRequest) {
      $('#cart-items').setAttribute(
        'aria-busy',
        'false'
      );
    }
  }
}

// Them / sua / xoa san pham
export async function mutate(path, method, body) {
  await authReady;

  if (!state.user) {
    requireLogin();
    return;
  }

  if (state.busy) return;

  const userId = state.user.user_id;
  const mutation = ++state.mutationId;

  setBusy(true);

  try {
    const data = await api(
      '/cart/' + encodeURIComponent(userId) + path,
      {
        method,
        body: body
          ? JSON.stringify(body)
          : undefined
      }
    );

    if (
      state.user?.user_id !== userId ||
      mutation !== state.mutationId
    ) return;

    state.cartRequest++;

    renderCart(data);
    message('Đã cập nhật giỏ hàng.');
    return true;

  } catch (error) {
    if (
      state.user?.user_id === userId &&
      mutation === state.mutationId
    ) {
      message(error.message, true);
    }

  } finally {
    if (mutation === state.mutationId) {
      setBusy(false);
    }
  }
}

// Gan su kien gio hang
export function bindCart() {
  $('#products').addEventListener('click', event => {
    const button = event.target.closest('[data-add]');

    if (button && !button.disabled) {
      mutate('/items', 'POST', {
        product_id: button.dataset.add,
        quantity: 1
      });
    }
  });

  $('#cart-items').addEventListener('click', event => {
    const button = event.target.closest('button');

    if (!button || button.disabled) return;

    if (button.dataset.remove) {
      mutate(
        '/items/' + encodeURIComponent(button.dataset.remove),
        'DELETE'
      );

    } else if (button.dataset.id) {
      mutate(
        '/items/' + encodeURIComponent(button.dataset.id),
        'PATCH',
        { quantity: Number(button.dataset.q) }
      );
    }
  });

  $('#clear').onclick = () => {
    if (state.user && state.cart?.items.length) {
      $('#clear-dialog').showModal();
    }
  };

  $('#cancel-clear').onclick = () =>
    $('#clear-dialog').close();

  $('#confirm-clear').onclick = () => {
    $('#clear-dialog').close();
    mutate('', 'DELETE');
  };
}
