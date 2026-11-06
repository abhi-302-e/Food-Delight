// ─── Foodie Delight Core App JS ──────────────────────────────────────────

let cart = JSON.parse(localStorage.getItem('fd_cart') || '[]');
let activeCoupon = null;

function saveCart() {
    localStorage.setItem('fd_cart', JSON.stringify(cart));
}

// ── Toast Notifications ──────────────────────────────────────────────────────
function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.className = 'toast ' + type + ' show';
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Cart State Operations ────────────────────────────────────────────────────
function addToCart(item) {
    const existing = cart.find(i => i.id === item.id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: parseFloat(item.price),
            image: item.image,
            category: item.category || '',
            quantity: 1
        });
    }
    saveCart();
    updateCartUI();
    showToast(`🛒 ${item.name} added to cart!`, 'success');
}

function removeFromCart(id) {
    cart = cart.filter(i => i.id !== id);
    saveCart();
    updateCartUI();
}

function changeQty(id, delta) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.quantity += delta;
    if (item.quantity <= 0) {
        removeFromCart(id);
    } else {
        saveCart();
        updateCartUI();
    }
}

// ── Coupon Application ───────────────────────────────────────────────────────
async function applyCoupon() {
    const codeInput = document.getElementById('couponCodeInput');
    const msgEl = document.getElementById('couponAppliedMsg');
    if (!codeInput) return;

    const code = codeInput.value.trim().toUpperCase();
    if (!code) {
        showToast('Please enter a promo code.', 'error');
        return;
    }

    const subtotal = cart.reduce((s, i) => s + i.price * i.quantity, 0);
    try {
        const res = await fetch('/api/coupon/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, total: subtotal })
        });
        const data = await res.json();
        if (data.valid) {
            activeCoupon = data;
            if (msgEl) {
                msgEl.textContent = `✅ ${data.code} applied: ${data.description}`;
                msgEl.style.display = 'block';
            }
            updateCartUI();
            showToast(`Coupon ${data.code} applied!`, 'success');
        } else {
            showToast(data.error || 'Invalid coupon code', 'error');
        }
    } catch(e) {
        showToast('Failed to validate coupon code', 'error');
    }
}

// ── Cart UI Rendering ────────────────────────────────────────────────────────
function updateCartUI() {
    const count = cart.reduce((s, i) => s + i.quantity, 0);
    document.querySelectorAll('.cart-count').forEach(el => el.textContent = count);

    const cartItems = document.getElementById('cartItems');
    const cartSubtotalEl = document.getElementById('cartSubtotal');
    const cartDiscountEl = document.getElementById('cartDiscount');
    const discountRow = document.getElementById('discountRow');
    const cartTotalEl = document.getElementById('cartTotal');

    if (!cartItems) return;

    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="empty-cart-message"><i class="fas fa-shopping-bag" style="font-size:2.5rem;color:#cbd5e1;margin-bottom:10px;display:block"></i>Your cart is empty. Explore our delicious menu!</div>';
        if (cartSubtotalEl) cartSubtotalEl.textContent = '0.00';
        if (cartTotalEl) cartTotalEl.textContent = '0.00';
        if (discountRow) discountRow.style.display = 'none';
        activeCoupon = null;
        return;
    }

    let subtotal = 0;
    cartItems.innerHTML = cart.map(item => {
        const itemSub = item.price * item.quantity;
        subtotal += itemSub;
        const imgSrc = resolveImgUrl(item.image);
        return `
            <div class="cart-item">
                <img src="${imgSrc}" alt="${escapeHtml(item.name)}" class="cart-thumb" onerror="this.src='/static/img/food-bg.jpg'">
                <div class="item-info">
                    <h4>${escapeHtml(item.name)}</h4>
                    <p class="item-price">$${item.price.toFixed(2)} each</p>
                    <div class="item-quantity">
                        <button class="quantity-btn minus" onclick="changeQty(${item.id}, -1)">−</button>
                        <span class="quantity">${item.quantity}</span>
                        <button class="quantity-btn plus" onclick="changeQty(${item.id}, 1)">+</button>
                    </div>
                </div>
                <div class="item-right-box">
                    <p class="item-total">$${itemSub.toFixed(2)}</p>
                    <button class="remove-item" onclick="removeFromCart(${item.id})" title="Remove item">&times;</button>
                </div>
            </div>
        `;
    }).join('');

    let discount = 0;
    if (activeCoupon) {
        if (activeCoupon.discount) {
            discount = activeCoupon.discount;
        }
        if (discountRow) {
            discountRow.style.display = 'flex';
            if (cartDiscountEl) cartDiscountEl.textContent = discount.toFixed(2);
        }
    } else {
        if (discountRow) discountRow.style.display = 'none';
    }

    const finalTotal = Math.max(0, subtotal - discount);

    if (cartSubtotalEl) cartSubtotalEl.textContent = subtotal.toFixed(2);
    if (cartTotalEl) cartTotalEl.textContent = finalTotal.toFixed(2);
}

function resolveImgUrl(url) {
    if (!url) return '/static/img/food-bg.jpg';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    if (url.startsWith('/')) return url;
    return '/static/' + url;
}

// ── Render Food Card Grid ────────────────────────────────────────────────────
function renderFoodGrid(items, containerId) {
    const grid = document.getElementById(containerId);
    if (!grid) return;

    if (!items || !items.length) {
        grid.innerHTML = `
            <div class="empty-food-state" style="grid-column: 1 / -1; text-align: center; padding: 60px 20px;">
                <i class="fas fa-search" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 14px; display: block;"></i>
                <h3 style="color: #334155; margin-bottom: 6px;">No dishes found</h3>
                <p style="color: #94a3b8;">Try adjusting your search terms or dietary filters.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = items.map(food => {
        const imgSrc = resolveImgUrl(food.image);
        return `
            <div class="food-card">
                <div class="food-img-wrap">
                    <img src="${imgSrc}" alt="${escapeHtml(food.name)}" loading="lazy" onerror="this.src='/static/img/food-bg.jpg'">
                    <span class="food-category-tag">${escapeHtml(food.category)}</span>
                    <div class="food-badges-overlay">
                        ${food.is_veg ? '<span class="badge-veg" title="Vegetarian">🌱 Veg</span>' : ''}
                        ${food.is_spicy ? '<span class="badge-spicy" title="Spicy">🌶️ Spicy</span>' : ''}
                        ${food.is_featured ? '<span class="badge-special" title="Chef Special">⭐ Chef Special</span>' : ''}
                    </div>
                </div>
                <div class="food-info">
                    <div class="food-rating-row">
                        <span class="stars"><i class="fas fa-star" style="color:#f59e0b"></i> ${food.rating || 4.8}</span>
                        <span class="prep-time"><i class="fas fa-clock"></i> ${escapeHtml(food.prep_time || '15-20 mins')}</span>
                    </div>
                    <h3>${escapeHtml(food.name)}</h3>
                    <p>${escapeHtml(food.description)}</p>
                    <div class="food-card-bottom">
                        <span class="price">$${parseFloat(food.price).toFixed(2)}</span>
                        <button class="add-to-cart" onclick='handleAddToCart(${JSON.stringify({
                            id: food.id,
                            name: food.name,
                            price: food.price,
                            image: food.image,
                            category: food.category
                        })})'>
                            <i class="fas fa-cart-plus"></i> Add
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ── Auth-Gated Add To Cart ───────────────────────────────────────────────────
function handleAddToCart(item) {
    if (!IS_LOGGED_IN) {
        openLoginRequired();
        return;
    }
    addToCart(item);
}

function openLoginRequired() {
    document.getElementById('loginRequiredModal')?.classList.add('open');
}
function closeLoginRequired() {
    document.getElementById('loginRequiredModal')?.classList.remove('open');
}

// ── Checkout Operations ──────────────────────────────────────────────────────
function openCart() {
    document.getElementById('cartModal')?.classList.add('open');
}
function closeCartModal() {
    document.getElementById('cartModal')?.classList.remove('open');
}

function openCheckout() {
    if (!IS_LOGGED_IN) {
        closeCartModal();
        openLoginRequired();
        return;
    }
    if (cart.length === 0) {
        showToast('Your cart is empty! Add some delicious dishes.', 'error');
        return;
    }
    closeCartModal();

    const subtotal = cart.reduce((s, i) => s + i.price * i.quantity, 0);
    const discount = activeCoupon ? (activeCoupon.discount || 0) : 0;
    const finalTotal = Math.max(0, subtotal - discount);

    const summary = document.getElementById('orderSummary');
    if (summary) {
        summary.innerHTML = `
            <h3><i class="fas fa-receipt"></i> Order Summary</h3>
            <div class="order-summary-items">
                ${cart.map(i => `
                    <div class="order-summary-item">
                        <span>${escapeHtml(i.name)} × ${i.quantity}</span>
                        <span>$${(i.price * i.quantity).toFixed(2)}</span>
                    </div>
                `).join('')}
            </div>
            ${discount > 0 ? `
                <div class="order-summary-item" style="color:#16a34a">
                    <span>Promo Discount (${activeCoupon.code})</span>
                    <span>-$${discount.toFixed(2)}</span>
                </div>
            ` : ''}
            <div class="order-summary-total">
                <span>Final Total:</span>
                <span>$${finalTotal.toFixed(2)}</span>
            </div>
        `;
    }
    openModal('checkoutModal');
}

async function confirmOrder() {
    const name = document.getElementById('co_name')?.value.trim();
    const phone = document.getElementById('co_phone')?.value.trim();
    const address = document.getElementById('co_address')?.value.trim();
    const notes = document.getElementById('co_notes')?.value.trim();
    const payment = document.getElementById('co_payment')?.value;
    const btn = document.getElementById('confirmOrder');

    if (!name) { showToast('Please enter your full name.', 'error'); return; }
    if (!address) { showToast('Please enter your delivery address.', 'error'); return; }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Placing Order...';

    const discount = activeCoupon ? (activeCoupon.discount || 0) : 0;

    try {
        const res = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_name: name,
                customer_phone: phone,
                address: address,
                notes: notes,
                payment_method: payment,
                discount: discount,
                items: cart
            })
        });
        const data = await res.json();

        if (res.status === 401 || data.login_required) {
            closeModal('checkoutModal');
            openLoginRequired();
        } else if (data.success) {
            closeModal('checkoutModal');
            document.getElementById('billOrderId').textContent = '#' + data.order_id;
            openModal('billModal');
            cart = [];
            activeCoupon = null;
            saveCart();
            updateCartUI();
            showToast('Order placed successfully! 🍕', 'success');
        } else {
            showToast(data.error || 'Order failed to place.', 'error');
        }
    } catch(e) {
        showToast('Network error while placing order.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Confirm &amp; Place Order';
    }
}

// ── Modal Utilities ──────────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ── Dom Ready Setup ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();

    // Mobile nav toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mainNav = document.getElementById('mainNav');
    mobileBtn?.addEventListener('click', () => {
        mainNav?.classList.toggle('nav-open');
    });

    // Cart Modal listeners
    document.getElementById('cartLink')?.addEventListener('click', e => { e.preventDefault(); openCart(); });
    document.getElementById('closeCart')?.addEventListener('click', closeCartModal);
    document.getElementById('checkoutBtn')?.addEventListener('click', openCheckout);
    document.getElementById('applyCouponBtn')?.addEventListener('click', applyCoupon);

    // Checkout Modal listeners
    document.getElementById('confirmOrder')?.addEventListener('click', confirmOrder);
    document.getElementById('cancelCheckout')?.addEventListener('click', () => { closeModal('checkoutModal'); openCart(); });
    document.getElementById('closeCheckout')?.addEventListener('click', () => closeModal('checkoutModal'));
    document.getElementById('closeBill')?.addEventListener('click', () => closeModal('billModal'));

    // Outside clicks
    window.addEventListener('click', e => {
        if (e.target === document.getElementById('cartModal')) closeCartModal();
        ['checkoutModal', 'billModal', 'loginRequiredModal'].forEach(id => {
            const el = document.getElementById(id);
            if (el && e.target === el) el.classList.remove('open');
        });
    });
});
