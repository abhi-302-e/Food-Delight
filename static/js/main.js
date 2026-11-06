// ─────────────────────────────────────────────
//  Foodie Delight — main.js
// ─────────────────────────────────────────────

let cart = JSON.parse(localStorage.getItem('fd_cart') || '[]');

// ── Auth helpers ──────────────────────────────
function getUser() {
  try { return JSON.parse(localStorage.getItem('fd_user')); } catch { return null; }
}

function updateAuthNav() {
  const user = getUser();
  const authLink    = document.getElementById('authLink');
  const adminLink   = document.getElementById('adminLink');
  const ordersLink  = document.getElementById('nav-orders');

  if (user) {
    authLink.innerHTML = `
      <span style="cursor:pointer;color:var(--primary);font-weight:600" onclick="logout()">
        👤 ${user.name.split(' ')[0]} · Logout
      </span>`;
    if (ordersLink) ordersLink.style.display = 'block';
    if (user.role === 'admin' && adminLink) adminLink.style.display = 'block';
  } else {
    authLink.innerHTML = '<a href="/login">Login / Register</a>';
    if (ordersLink) ordersLink.style.display = 'none';
    if (adminLink)  adminLink.style.display  = 'none';
  }
}

function logout() {
  localStorage.removeItem('fd_user');
  showToast('👋 Logged out', 'success');
  setTimeout(() => window.location.href = '/', 800);
}

// ── Active nav link ───────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  const map = {'/':'nav-home','/menu':'nav-menu','/about':'nav-about','/contact':'nav-contact','/orders':'nav-orders'};
  const id = map[path];
  if (id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  }
}

// ── Toast ─────────────────────────────────────
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = `toast toast-${type} show`;
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Cart helpers ──────────────────────────────
function saveCart() {
  localStorage.setItem('fd_cart', JSON.stringify(cart));
  updateCartBadge();
  renderCartSidebar();
}

function updateCartBadge() {
  const total = cart.reduce((sum, i) => sum + i.quantity, 0);
  document.getElementById('cartCount').textContent = total;
}

function addToCart(food) {
  const existing = cart.find(i => i.id === food.id);
  if (existing) { existing.quantity++; }
  else { cart.push({ ...food, quantity: 1 }); }
  saveCart();
  showToast(`🛒 ${food.name} added to cart!`, 'success');

  // Bounce animation on button
  const btn = document.querySelector(`[data-cart-id="${food.id}"]`);
  if (btn) { btn.classList.add('added'); setTimeout(() => btn.classList.remove('added'), 600); }
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  saveCart();
}

function changeQty(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) removeFromCart(id);
  else saveCart();
}

function renderCartSidebar() {
  const el     = document.getElementById('cartItems');
  const total  = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  document.getElementById('cartTotal').textContent = total.toFixed(2);

  if (!cart.length) {
    el.innerHTML = `<div class="empty-cart"><i class="fas fa-shopping-bag"></i><p>Your cart is empty</p></div>`;
    return;
  }
  el.innerHTML = cart.map(item => `
    <div class="cart-item">
      <img src="/static/${item.image}" alt="${item.name}" onerror="this.src='/static/img/food-bg.jpg'">
      <div class="cart-item-info">
        <h4>${item.name}</h4>
        <span class="cart-item-price">$${item.price.toFixed(2)}</span>
        <div class="qty-controls">
          <button onclick="changeQty(${item.id},-1)">−</button>
          <span>${item.quantity}</span>
          <button onclick="changeQty(${item.id},1)">+</button>
        </div>
      </div>
      <div class="cart-item-right">
        <button class="remove-item" onclick="removeFromCart(${item.id})"><i class="fas fa-trash"></i></button>
        <span class="cart-item-total">$${(item.price * item.quantity).toFixed(2)}</span>
      </div>
    </div>`).join('');
}

function openCart() {
  document.getElementById('cartSidebar').classList.add('open');
  document.getElementById('cartOverlay').classList.add('show');
}
function closeCartFn() {
  document.getElementById('cartSidebar').classList.remove('open');
  document.getElementById('cartOverlay').classList.remove('show');
}

// ── Checkout ──────────────────────────────────
function openCheckout() {
  if (!cart.length) { showToast('🛒 Your cart is empty!', 'error'); return; }
  closeCartFn();

  const user = getUser();
  if (user) {
    document.getElementById('co-name').value  = user.name  || '';
    document.getElementById('co-email').value = user.email || '';
  }

  const total = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  document.getElementById('finalTotal').textContent = total.toFixed(2);
  document.getElementById('orderSummary').innerHTML = cart.map(i => `
    <div class="summary-row">
      <span>${i.name} × ${i.quantity}</span>
      <span>$${(i.price * i.quantity).toFixed(2)}</span>
    </div>`).join('') + `<hr><div class="summary-row"><strong>Total</strong><strong>$${total.toFixed(2)}</strong></div>`;

  document.getElementById('checkoutOverlay').style.display = 'flex';
}

async function placeOrder() {
  const name    = document.getElementById('co-name').value.trim();
  const email   = document.getElementById('co-email').value.trim();
  const phone   = document.getElementById('co-phone').value.trim();
  const address = document.getElementById('co-address').value.trim();

  if (!name || !email) { showToast('❌ Name and email are required', 'error'); return; }

  const user  = getUser();
  const total = cart.reduce((s, i) => s + i.price * i.quantity, 0);

  const btn = document.getElementById('placeOrderBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Placing Order...';

  try {
    const res = await fetch('/api/orders', {
      method:  'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        items:      cart,
        total:      total,
        user_id:    user?.id,
        user_name:  name,
        user_email: email,
        phone,
        address
      })
    });
    const data = await res.json();
    if (res.ok) {
      cart = [];
      saveCart();
      document.getElementById('checkoutOverlay').style.display = 'none';
      showToast('🎉 Order #' + data.order.id + ' placed successfully!', 'success');
    } else {
      showToast('❌ ' + data.error, 'error');
    }
  } catch { showToast('❌ Network error', 'error'); }

  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-check-circle"></i> Place Order';
}

// ── Food card builder ─────────────────────────
function buildFoodCard(food) {
  return `
    <div class="food-card">
      <div class="food-card-img">
        <img src="/static/${food.image}" alt="${food.name}" loading="lazy"
             onerror="this.src='/static/img/food-bg.jpg'">
        <span class="food-cat-badge">${food.category}</span>
      </div>
      <div class="food-card-body">
        <h3>${food.name}</h3>
        <p>${food.description}</p>
        <div class="food-card-footer">
          <span class="food-price">$${food.price.toFixed(2)}</span>
          <button class="btn-add-cart" data-cart-id="${food.id}"
            onclick='addToCart(${JSON.stringify(food)})'>
            <i class="fas fa-plus"></i> Add
          </button>
        </div>
      </div>
    </div>`;
}

function attachAddToCartListeners() {
  // handled via inline onclick in buildFoodCard
}

// ── Init ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  updateAuthNav();
  setActiveNav();
  updateCartBadge();
  renderCartSidebar();

  // Cart open/close
  document.getElementById('cartLink').addEventListener('click', (e) => {
    e.preventDefault();
    openCart();
  });
  document.getElementById('closeCart').addEventListener('click', closeCartFn);
  document.getElementById('cartOverlay').addEventListener('click', closeCartFn);

  // Checkout
  document.getElementById('checkoutBtn').addEventListener('click', openCheckout);
  document.getElementById('placeOrderBtn').addEventListener('click', placeOrder);
  document.getElementById('closeCheckout').addEventListener('click', () => {
    document.getElementById('checkoutOverlay').style.display = 'none';
  });
  document.getElementById('checkoutOverlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('checkoutOverlay')) {
      document.getElementById('checkoutOverlay').style.display = 'none';
    }
  });
});
