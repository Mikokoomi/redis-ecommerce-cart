/* RedisCart — giao diện tài khoản (Đăng ký / Đăng nhập / Đăng xuất).
   Dùng API /api/auth/* hiện có; KHÔNG tự thay đổi quyền truy cập giỏ hàng. */
(() => {
  'use strict';

  const header = document.querySelector('.header-inner');
  if (!header || document.getElementById('auth-dialog')) return;
  const $ = (id) => document.getElementById(id);

  const actions = document.createElement('div');
  actions.className = 'auth-actions';
  actions.innerHTML = `
    <button type="button" id="auth-open" class="auth-open-btn">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-4.1 3-6.5 7-6.5s7 2.4 7 6.5"/></svg>
      <span>Đăng nhập</span>
    </button>
    <div id="auth-user" class="auth-profile" hidden>
      <span class="auth-avatar" id="auth-avatar" aria-hidden="true">R</span>
      <span id="auth-username" class="auth-profile-name"></span>
      <button type="button" id="auth-logout" class="auth-logout-btn">Đăng xuất</button>
    </div>`;
  header.appendChild(actions);

  const dialog = document.createElement('dialog');
  dialog.id = 'auth-dialog';
  dialog.setAttribute('aria-labelledby', 'auth-title');
  dialog.innerHTML = `
    <div class="auth-shell">
      <aside class="auth-showcase" aria-hidden="true">
        <div class="auth-showcase-top">
          <span class="auth-brand-mark"><svg viewBox="0 0 28 28"><path d="m14 2 12 7-12 7L2 9Zm-12 12 12 7 12-7M2 19l12 7 12-7"/></svg></span>
          <span class="auth-brand-name">RedisCart<span>.</span></span>
        </div>
        <div class="auth-showcase-center">
          <div class="auth-showcase-tag"><span></span> REDISCART EXPERIENCE</div>
          <h3>Mua sắm công nghệ<br><em>theo cách của bạn.</em></h3>
          <p>Khám phá sản phẩm, quản lý giỏ hàng và trải nghiệm mua sắm dễ dàng hơn mỗi ngày.</p>
          <div class="auth-illustration">
            <div class="auth-illustration-glow"></div>
            <div class="auth-mini-card auth-mini-card-back"><span>REDISCART</span><strong>TECH</strong><small>Đơn giản &amp; tiện lợi</small></div>
            <div class="auth-mini-card auth-mini-card-front"><span class="auth-mini-icon">✦</span><strong>Giỏ hàng</strong><small>Được lưu bằng Redis</small><div class="auth-mini-bars"><i></i><i></i><i></i></div></div>
          </div>
        </div>
        <div class="auth-showcase-bottom"><span class="auth-showcase-dot"></span> Cửa hàng công nghệ RedisCart</div>
      </aside>
      <section class="auth-main">
        <button type="button" id="auth-close" class="auth-close" aria-label="Đóng cửa sổ">×</button>
        <div class="auth-content">
          <div class="auth-form-kicker">TÀI KHOẢN REDISCART</div>
          <h2 id="auth-title">Chào mừng trở lại</h2>
          <p id="auth-subtitle" class="auth-subtitle">Đăng nhập để tiếp tục trải nghiệm mua sắm.</p>
          <form id="auth-form">
            <label id="auth-name-label" class="auth-field" hidden>
              <span>Họ và tên</span>
              <span class="auth-input-wrap">
                <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c0-4 3-6 7-6s7 2 7 6"/></svg>
                <input id="auth-name" type="text" autocomplete="name" placeholder="Nguyễn Văn A" minlength="2" maxlength="80">
              </span>
            </label>
            <label class="auth-field">
              <span>Email</span>
              <span class="auth-input-wrap">
                <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 7 9-7"/></svg>
                <input id="auth-email" type="email" autocomplete="email" placeholder="tenban@example.com" required>
              </span>
            </label>
            <label class="auth-field">
              <span>Mật khẩu</span>
              <span class="auth-input-wrap">
                <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>
                <input id="auth-password" type="password" minlength="8" maxlength="128" autocomplete="current-password" placeholder="Nhập mật khẩu" required>
                <button type="button" class="auth-password-toggle" id="auth-password-toggle" aria-label="Hiện mật khẩu" aria-pressed="false">
                  <svg class="eye-show" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg class="eye-hide" viewBox="0 0 24 24" aria-hidden="true" hidden><path d="M3 3l18 18M10.6 6.1A11 11 0 0 1 12 6c6.5 0 10 6 10 6a13 13 0 0 1-3.2 3.8M6.1 6.1C3.5 8.2 2 12 2 12s3.5 6 10 6c1.6 0 3-.3 4.2-.9"/><path d="M10 10a3 3 0 0 0 4 4"/></svg>
                </button>
              </span>
            </label>
            <p id="auth-error" role="alert" hidden></p>
            <button type="submit" id="auth-submit" class="auth-submit">Đăng nhập</button>
          </form>
          <div class="auth-switch-line">
            <span id="auth-switch-text">Chưa có tài khoản?</span>
            <button type="button" id="auth-switch">Đăng ký ngay</button>
          </div>
          <div class="auth-form-footer"><span>✦</span> Trải nghiệm mua sắm dành cho đồ án RedisCart</div>
        </div>
      </section>
    </div>`;
  document.body.appendChild(dialog);

// ========================================
// DROPDOWN TAI KHOAN REDISCART
// ========================================

const profile = $('auth-user');

const accountTrigger = document.createElement('button');
accountTrigger.type = 'button';
accountTrigger.id = 'account-trigger';
accountTrigger.className = 'account-trigger';

accountTrigger.setAttribute('aria-haspopup', 'true');
accountTrigger.setAttribute('aria-expanded', 'false');
accountTrigger.setAttribute(
  'aria-controls',
  'account-menu'
);

// Ten tai khoan
const accountName = document.createElement('span');
accountName.className = 'account-name';

accountName.appendChild($('auth-username'));

// Icon mui ten nho
const accountArrow = document.createElement('span');
accountArrow.className = 'account-arrow';
accountArrow.setAttribute('aria-hidden', 'true');

accountArrow.innerHTML = `
  <svg viewBox="0 0 24 24">
    <path d="m6 9 6 6 6-6"/>
  </svg>
`;

// Su dung avatar va ten da co san
accountTrigger.append(
  $('auth-avatar'),
  accountName,
  accountArrow
);

// Tao menu xo xuong
const accountMenu = document.createElement('div');
accountMenu.id = 'account-menu';
accountMenu.className = 'account-menu';
accountMenu.hidden = true;

accountMenu.innerHTML = `
  <div class="account-menu-info">
    <span class="account-menu-label">
      TÀI KHOẢN CỦA TÔI
    </span>

    <strong id="account-menu-name"></strong>
    <small id="account-menu-email"></small>
  </div>

  <div class="account-menu-links">
    <a href="#cart" class="account-menu-link">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 7h14l1 14H4L5 7Z"/>
        <path d="M9 8V6a3 3 0 0 1 6 0v2"/>
      </svg>
      Giỏ hàng của tôi
    </a>

    <a href="#catalog" class="account-menu-link">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 5h16v14H4z"/>
        <path d="M4 10h16M10 10v9"/>
      </svg>
      Tiếp tục mua sắm
    </a>
  </div>

  <div class="account-menu-bottom"
       id="account-logout-place">
  </div>
`;

// Di chuyen nut Dang xuat cu vao menu
accountMenu.querySelector(
  '#account-logout-place'
).appendChild($('auth-logout'));

// Gan menu vao khu vuc tai khoan
profile.append(
  accountTrigger,
  accountMenu
);

// Dong menu
function closeAccountMenu() {
  accountMenu.hidden = true;
  accountTrigger.setAttribute(
    'aria-expanded',
    'false'
  );
}

// Bam vao tai khoan de mo/dong
accountTrigger.addEventListener('click', () => {
  const willOpen = accountMenu.hidden;

  accountMenu.hidden = !willOpen;

  accountTrigger.setAttribute(
    'aria-expanded',
    String(willOpen)
  );
});

// Bam ra ngoai dong menu
document.addEventListener('click', event => {
  if (!profile.contains(event.target)) {
    closeAccountMenu();
  }
});

// Nhan Escape dong menu
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !accountMenu.hidden) {
    closeAccountMenu();
    accountTrigger.focus();
  }
});

// Chuyen trang thi dong menu
window.addEventListener(
  'hashchange',
  closeAccountMenu
);

// Dang xuat thi dong menu
$('auth-logout').addEventListener(
  'click',
  closeAccountMenu
);

// Cap nhat thong tin khi dang nhap
window.addEventListener(
  'rediscart:auth-changed',
  event => {
    const user = event.detail;

    $('account-menu-name').textContent =
      user?.name || '';

    $('account-menu-email').textContent =
      user?.email || '';

    closeAccountMenu();
  }
);

  let mode = 'login';
  let busy = false;

  function setMode(next) {
    mode = next;
    const register = next === 'register';
    $('auth-title').textContent = register ? 'Tạo tài khoản mới' : 'Chào mừng trở lại';
    $('auth-subtitle').textContent = register
      ? 'Tạo tài khoản để bắt đầu khám phá RedisCart.'
      : 'Đăng nhập để tiếp tục trải nghiệm mua sắm.';
    $('auth-name-label').hidden = !register;
    $('auth-name').required = register;
    $('auth-password').autocomplete = register ? 'new-password' : 'current-password';
    $('auth-switch-text').textContent = register ? 'Đã có tài khoản?' : 'Chưa có tài khoản?';
    $('auth-switch').textContent = register ? 'Đăng nhập' : 'Đăng ký ngay';
    $('auth-submit').textContent = register ? 'Tạo tài khoản' : 'Đăng nhập';
    $('auth-error').hidden = true;
    setPasswordVisible(false);
  }

  let authRevision = 0;
  function showUser(user) {
    authRevision++;
    $('auth-open').hidden = Boolean(user);
    $('auth-user').hidden = !user;
    $('auth-username').textContent = user ? user.name : '';
    $('auth-avatar').textContent = user ? (user.name || 'K').trim().charAt(0).toUpperCase() : 'K';
    window.dispatchEvent(new CustomEvent('rediscart:auth-changed', {detail: user}));
  }

  async function callAuth(endpoint, method = 'GET', payload) {
    const response = await fetch('/api/auth/' + endpoint, {
      method,
      credentials: 'same-origin',
      headers: payload ? { 'Content-Type': 'application/json' } : undefined,
      body: payload ? JSON.stringify(payload) : undefined
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const msg = typeof data.detail === 'string'
        ? data.detail
        : `Yêu cầu không thành công (HTTP ${response.status}).`;
      throw new Error(msg);
    }
    return data;
  }

  function openLogin() {
    $('auth-form').reset();
    setPasswordVisible(false);
    setMode('login');
    dialog.showModal();
    $('auth-email').focus();
  }
  $('auth-open').addEventListener('click', openLogin);
  window.addEventListener('rediscart:open-login', openLogin);
  window.addEventListener('rediscart:auth-expired', () => showUser(null));
  $('auth-close').addEventListener('click', () => dialog.close());
  $('auth-switch').addEventListener('click', () => {
    if (busy) return;
    setMode(mode === 'login' ? 'register' : 'login');
    (mode === 'register' ? $('auth-name') : $('auth-email')).focus();
  });
  function setPasswordVisible(visible) {
    $('auth-password').type = visible ? 'text' : 'password';
    $('auth-password-toggle').setAttribute('aria-label', visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
    $('auth-password-toggle').setAttribute('aria-pressed', String(visible));
    $('auth-password-toggle').querySelector('.eye-show').hidden = visible;
    $('auth-password-toggle').querySelector('.eye-hide').hidden = !visible;
  }
  $('auth-password-toggle').addEventListener('click', () => {
    setPasswordVisible($('auth-password').type === 'password');
  });

  $('auth-logout').addEventListener('click', async () => {
    try {
      await callAuth('logout', 'POST');
      showUser(null);
    } catch (error) {
      alert('Không thể đăng xuất: ' + error.message);
    }
  });

  $('auth-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy) return;
    busy = true;
    const submit = $('auth-submit');
    $('auth-error').hidden = true;
    submit.disabled = true;
    const previous = submit.innerHTML;
    submit.textContent = 'Đang xử lý...';
    try {
      const email = $('auth-email').value.trim();
      const password = $('auth-password').value;
      if (mode === 'register') {
        await callAuth('register', 'POST', {
          name: $('auth-name').value.trim(), email, password
        });
      }
      const user = await callAuth('login', 'POST', { email, password });
      showUser(user);
      $('auth-password').value = '';
      dialog.close();
    } catch (error) {
      $('auth-error').textContent = error.message;
      $('auth-error').hidden = false;
    } finally {
      submit.disabled = false;
      submit.innerHTML = previous;
      busy = false;
    }
  });

  callAuth('me').then(user => {
    if (authRevision === 0) showUser(user);
  }).catch(() => {
    if (authRevision === 0) showUser(null);
  });
})();
