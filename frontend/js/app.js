
import { $, message } from './modules/core.js';
import { bindAuth } from './modules/auth-state.js';
import {
  bindCatalog, loadProducts, loadDetail
} from './modules/products.js';
import { bindCart, loadCart } from './modules/cart.js';
import {
  bindCheckout, prepareCheckout, loadOrder
} from './modules/checkout.js';

// Dieu huong cac trang RedisCart
function route() {
  const hash = location.hash;

  const cart = hash === '#cart';
  const detail = hash.startsWith('#product/');
  const checkout = hash === '#checkout';
  const order = hash.startsWith('#order/');

  $('#catalog-view').hidden =
    cart || detail || checkout || order;

  $('#cart-view').hidden = !cart;
  $('#detail-view').hidden = !detail;
  $('#checkout-view').hidden = !checkout;
  $('#order-view').hidden = !order;

  document.title = cart
    ? 'Giỏ hàng — RedisCart'
    : detail
      ? 'Chi tiết sản phẩm — RedisCart'
      : checkout
        ? 'Xác nhận mua hàng — RedisCart'
        : 'RedisCart';

  if (cart) loadCart();

  if (detail) {
    loadDetail(decodeURIComponent(hash.slice(9)));
  }

  if (checkout) prepareCheckout();
  if (order) loadOrder(hash.slice(7));
}

// Khoi tao cac chuc nang
bindCatalog();
bindCart();
bindCheckout();
bindAuth(() => loadCart());

// Tai lai du lieu
$('#retry').onclick = () => {
  message('');
  loadProducts();
  loadCart();
};

// Chuyen trang
window.addEventListener('hashchange', () => {
  route();

  window.scrollTo({
    top: 0,
    behavior: 'instant'
  });

  if (location.hash === '#cart') {
    $('#cart-heading').focus({
      preventScroll: true
    });
  }
});

// Khoi dong
route();
loadProducts();

if (location.hash !== '#cart') {
  loadCart();
}
