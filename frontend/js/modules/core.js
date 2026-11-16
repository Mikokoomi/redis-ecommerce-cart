
export const $ = selector =>
  document.querySelector(selector);

export const categories = {
  '': 'Tất cả',
  'dien-thoai': 'Điện thoại',
  laptop: 'Laptop',
  'tai-nghe': 'Tai nghe',
  'dong-ho': 'Đồng hồ',
  'phu-kien': 'Phụ kiện'
};

// Trang thai duoc chia se giua cac module
export const state = {
  user: null,
  authVersion: 0,
  cartRequest: 0,
  mutationId: 0,
  cart: null,
  busy: false,
  selected: '',
  query: '',
  productRequest: 0,
  detailRequest: 0,
  checkoutKey: '',
  checkoutBusy: false
};

export const money = value =>
  new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND'
  }).format(value);

export const esc = value =>
  String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));

export const image = product =>
  /^\/assets\/images\/products\/SP[0-9]{3}\.webp$/.test(
    product.image || ''
  )
    ? product.image
    : '/assets/phu-kien.svg';

export const bagIcon = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 7h14l1 14H4L5 7Z"/>
    <path d="M9 8V6a3 3 0 0 1 6 0v2"/>
  </svg>
`;

export const plusIcon = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 5v14M5 12h14"/>
  </svg>
`;

export function empty(title, description) {
  return `
    <div class="empty-state">
      ${bagIcon}
      <h2>${esc(title)}</h2>
      <p>${esc(description)}</p>
    </div>
  `;
}

export function setupImages(root) {
  root.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', () => {
      if (
        img.getAttribute('src') ===
        '/assets/phu-kien.svg'
      ) return;

      img.src = '/assets/phu-kien.svg';
      img.alt = 'Không tải được ảnh ' + img.alt;
      img.classList.add('image-error');

      const note = document.createElement('span');
      note.className = 'image-error-note';
      note.textContent = 'Ảnh tạm thời không khả dụng';
      img.parentElement.append(note);
    }, { once: true });
  });
}

let messageTimer;

export function message(content, isError = false) {
  clearTimeout(messageTimer);

  $('#message').textContent = content;
  $('#message').className = isError ? 'error' : '';

  if (content && !isError) {
    messageTimer = setTimeout(() => {
      $('#message').textContent = '';
    }, 4500);
  }
}

// Goi API FastAPI
export async function api(path, options = {}) {
  const controller = new AbortController();

  const timeout = setTimeout(
    () => controller.abort(),
    15000
  );

  try {
    const response = await fetch('/api' + path, {
      ...options,
      credentials: 'same-origin',
      signal: controller.signal,
      headers: {
        ...(options.body
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(options.headers || {})
      }
    });

    const data = await response.json()
      .catch(() => ({}));

    if (!response.ok) {
      if (
        response.status === 401 &&
        state.user &&
        path.startsWith(
          '/cart/' +
          encodeURIComponent(state.user.user_id)
        )
      ) {
        state.authVersion++;
        state.user = null;

        window.dispatchEvent(
          new Event('rediscart:auth-expired')
        );
      }

      throw Error(
        typeof data.detail === 'string'
          ? data.detail
          : `Không thể xử lý yêu cầu (HTTP ${response.status}).`
      );
    }

    return data;

  } catch (error) {
    if (error.name === 'AbortError') {
      throw Error(
        'Kết nối quá lâu. Vui lòng thử lại.'
      );
    }

    throw error;

  } finally {
    clearTimeout(timeout);
  }
}
