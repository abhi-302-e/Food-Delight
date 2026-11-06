// ─── Foodie Delight Admin Dashboard JS ───────────────────────────────────

let adminState = {
    orders: [],
    menu: [],
    reservations: [],
    messages: [],
    users: [],
    currentTab: 'overview',
    orderStatusFilter: 'all',
    menuCatFilter: 'all'
};

// ── Toast Helper ─────────────────────────────────────────────────────────────
function adminToast(msg, type = 'success') {
    const t = document.getElementById('adminToast');
    if (!t) return;
    t.textContent = msg;
    t.className = 'toast ' + type + ' show';
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Tab Switching ────────────────────────────────────────────────────────────
function switchTab(tabName) {
    adminState.currentTab = tabName;
    document.querySelectorAll('.admin-nav-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.admin-tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `pane-${tabName}`);
    });
}

// ── Modal Helpers ────────────────────────────────────────────────────────────
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

// ── Data Fetching ────────────────────────────────────────────────────────────
async function loadAllAdminData() {
    await Promise.all([
        fetchStats(),
        fetchOrders(),
        fetchMenu(),
        fetchReservations(),
        fetchMessages(),
        fetchUsers()
    ]);
}

async function fetchStats() {
    try {
        const res = await fetch('/api/admin/stats');
        const data = await res.json();
        document.getElementById('statRevenue').textContent = '$' + parseFloat(data.revenue).toFixed(2);
        document.getElementById('statOrders').textContent = data.total_orders;
        document.getElementById('statPending').textContent = data.pending_orders;
        document.getElementById('statDelivered').textContent = data.delivered_orders;
        document.getElementById('statItems').textContent = data.total_items;
        document.getElementById('statReservations').textContent = data.total_reservations;

        document.getElementById('badgePendingOrders').textContent = data.pending_orders;
        document.getElementById('badgeMessages').textContent = data.unread_messages;
    } catch(e) {
        console.error('Error fetching stats:', e);
    }
}

// ── Orders Handling ──────────────────────────────────────────────────────────
async function fetchOrders() {
    try {
        const res = await fetch('/api/admin/orders');
        adminState.orders = await res.json();
        renderRecentOrders();
        renderMasterOrders();
    } catch(e) {
        console.error('Error fetching orders:', e);
    }
}

function renderRecentOrders() {
    const tbody = document.querySelector('#recentOrdersTable tbody');
    if (!tbody) return;
    const recent = adminState.orders.slice(0, 5);
    if (!recent.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:#94a3b8">No orders yet</td></tr>';
        return;
    }
    tbody.innerHTML = recent.map(o => `
        <tr>
            <td><strong>#${o.id}</strong></td>
            <td>
                <strong>${escapeHtml(o.customer_name)}</strong><br>
                <small style="color:#64748b">${escapeHtml(o.customer_email)}</small>
            </td>
            <td><strong>$${parseFloat(o.total).toFixed(2)}</strong></td>
            <td><span class="status-badge status-${o.status}">${formatStatus(o.status)}</span></td>
            <td>${o.created_at}</td>
            <td><button class="btn-text-link" onclick="viewOrderModal(${o.id})">Details</button></td>
        </tr>
    `).join('');
}

function renderMasterOrders() {
    const tbody = document.getElementById('ordersMasterBody');
    if (!tbody) return;

    const filter = adminState.orderStatusFilter;
    const query = document.getElementById('orderSearchInput')?.value.trim().toLowerCase() || '';

    let filtered = adminState.orders;
    if (filter !== 'all') {
        filtered = filtered.filter(o => o.status === filter);
    }
    if (query) {
        filtered = filtered.filter(o => 
            o.id.toString().includes(query) || 
            o.customer_name.toLowerCase().includes(query) || 
            o.customer_email.toLowerCase().includes(query)
        );
    }

    if (!filtered.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:#94a3b8">No matching orders found</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(o => {
        const itemsSummary = o.items ? o.items.map(i => `${i.name} (x${i.quantity})`).join(', ') : 'Details';
        return `
            <tr>
                <td><strong>#${o.id}</strong></td>
                <td>
                    <strong>${escapeHtml(o.customer_name)}</strong><br>
                    <small style="color:#64748b"><i class="fas fa-phone-alt" style="font-size:0.75rem"></i> ${escapeHtml(o.customer_phone || 'N/A')}</small><br>
                    <small style="color:#94a3b8">${escapeHtml(o.customer_email)}</small>
                </td>
                <td style="max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis" title="${escapeHtml(itemsSummary)}">
                    ${escapeHtml(itemsSummary)}
                </td>
                <td><strong>$${parseFloat(o.total).toFixed(2)}</strong></td>
                <td><small style="font-weight:600">${escapeHtml(o.payment_method || 'Cash on Delivery')}</small></td>
                <td><span class="status-badge status-${o.status}">${formatStatus(o.status)}</span></td>
                <td><small>${o.created_at}</small></td>
                <td>
                    <select class="status-select" onchange="updateOrderStatus(${o.id}, this.value)">
                        <option value="pending" ${o.status==='pending'?'selected':''}>Pending</option>
                        <option value="confirmed" ${o.status==='confirmed'?'selected':''}>Confirmed</option>
                        <option value="preparing" ${o.status==='preparing'?'selected':''}>Preparing</option>
                        <option value="out_for_delivery" ${o.status==='out_for_delivery'?'selected':''}>Out for Delivery</option>
                        <option value="delivered" ${o.status==='delivered'?'selected':''}>Delivered</option>
                        <option value="cancelled" ${o.status==='cancelled'?'selected':''}>Cancelled</option>
                    </select>
                    <button class="btn-action-icon" style="margin-left:6px" onclick="viewOrderModal(${o.id})" title="View Details"><i class="fas fa-eye"></i></button>
                </td>
            </tr>
        `;
    }).join('');
}

async function updateOrderStatus(orderId, newStatus) {
    try {
        const res = await fetch(`/api/admin/orders/${orderId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            adminToast(`Order #${orderId} marked as ${formatStatus(newStatus)}!`, 'success');
            await fetchStats();
            await fetchOrders();
        } else {
            adminToast(data.error || 'Failed to update order', 'error');
        }
    } catch(e) {
        adminToast('Network error while updating status', 'error');
    }
}

function viewOrderModal(orderId) {
    const order = adminState.orders.find(o => o.id === orderId);
    if (!order) return;

    document.getElementById('adminOrderDetailId').textContent = '#' + order.id;
    const content = document.getElementById('adminOrderModalContent');
    const items = order.items || [];

    content.innerHTML = `
        <div style="background:#f8fafc; border-radius:10px; padding:14px; margin-bottom:16px; font-size:0.88rem">
            <p><strong>Customer:</strong> ${escapeHtml(order.customer_name)}</p>
            <p><strong>Email:</strong> ${escapeHtml(order.customer_email)}</p>
            <p><strong>Phone:</strong> ${escapeHtml(order.customer_phone || 'N/A')}</p>
            <p><strong>Address:</strong> ${escapeHtml(order.address || 'N/A')}</p>
            <p><strong>Payment:</strong> ${escapeHtml(order.payment_method || 'Cash on Delivery')}</p>
            ${order.notes ? `<p><strong>Notes:</strong> <em>${escapeHtml(order.notes)}</em></p>` : ''}
            <p><strong>Placed:</strong> ${order.created_at}</p>
        </div>
        <table class="admin-table" style="margin-bottom:14px">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Price</th>
                    <th>Qty</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
                ${items.map(i => `
                    <tr>
                        <td><strong>${escapeHtml(i.name)}</strong></td>
                        <td>$${parseFloat(i.price).toFixed(2)}</td>
                        <td>${i.quantity}</td>
                        <td><strong>$${(parseFloat(i.price)*i.quantity).toFixed(2)}</strong></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="text-align:right; font-size:1.15rem; font-weight:800; color:var(--admin-primary)">
            Total: $${parseFloat(order.total).toFixed(2)}
        </div>
    `;
    openModal('adminOrderModal');
}

// ── Menu Management ──────────────────────────────────────────────────────────
async function fetchMenu() {
    try {
        const res = await fetch('/api/admin/menu');
        adminState.menu = await res.json();
        renderMenuMaster();
    } catch(e) {
        console.error('Error fetching menu:', e);
    }
}

function renderMenuMaster() {
    const tbody = document.getElementById('menuMasterBody');
    if (!tbody) return;

    const cat = adminState.menuCatFilter;
    const search = document.getElementById('menuSearchInput')?.value.trim().toLowerCase() || '';

    let items = adminState.menu;
    if (cat !== 'all') {
        items = items.filter(i => i.category === cat);
    }
    if (search) {
        items = items.filter(i => i.name.toLowerCase().includes(search) || i.description.toLowerCase().includes(search));
    }

    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:#94a3b8">No menu items found</td></tr>';
        return;
    }

    tbody.innerHTML = items.map(item => `
        <tr>
            <td>
                <img class="table-thumb" src="${item.image}" alt="${escapeHtml(item.name)}" onerror="this.src='/static/img/food-bg.jpg'">
            </td>
            <td>
                <strong>${escapeHtml(item.name)}</strong><br>
                <small style="color:#64748b;display:inline-block;max-width:240px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap">${escapeHtml(item.description)}</small>
            </td>
            <td><span class="status-badge" style="background:#f1f5f9;color:#475569">${item.category}</span></td>
            <td><strong>$${parseFloat(item.price).toFixed(2)}</strong></td>
            <td>
                ${item.is_veg ? '<span title="Vegetarian" style="cursor:default">🌱</span> ' : ''}
                ${item.is_spicy ? '<span title="Spicy" style="cursor:default">🌶️</span> ' : ''}
                ${item.is_featured ? '<span title="Chef Special" style="cursor:default">⭐</span>' : ''}
            </td>
            <td><small>${escapeHtml(item.prep_time || '15 mins')}</small></td>
            <td>
                <label class="toggle-switch">
                    <input type="checkbox" ${item.available ? 'checked' : ''} onchange="toggleMenuItem(${item.id})">
                    <span class="slider"></span>
                </label>
            </td>
            <td>
                <button class="btn-action-icon edit" onclick="openEditMenuModal(${item.id})" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="btn-action-icon delete" onclick="deleteMenuItem(${item.id}, '${escapeHtml(item.name)}')" title="Delete"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>
    `).join('');
}

async function toggleMenuItem(id) {
    try {
        const res = await fetch(`/api/admin/menu/${id}/toggle`, { method: 'PUT' });
        const data = await res.json();
        if (data.success) {
            adminToast(`Item availability updated!`, 'success');
            await fetchMenu();
        }
    } catch(e) {
        adminToast('Failed to toggle availability', 'error');
    }
}

function openAddMenuModal() {
    document.getElementById('menuModalTitle').innerHTML = '<i class="fas fa-plus-circle"></i> Add New Dish';
    document.getElementById('item_id').value = '';
    document.getElementById('item_name').value = '';
    document.getElementById('item_price').value = '';
    document.getElementById('item_category').value = 'pizza';
    document.getElementById('item_prep').value = '15-20 mins';
    document.getElementById('item_rating').value = '4.8';
    document.getElementById('item_image').value = '';
    document.getElementById('item_description').value = '';
    document.getElementById('item_veg').checked = false;
    document.getElementById('item_spicy').checked = false;
    document.getElementById('item_featured').checked = false;
    document.getElementById('itemImgPreview').style.display = 'none';
    openModal('menuItemModal');
}

function openEditMenuModal(id) {
    const item = adminState.menu.find(i => i.id === id);
    if (!item) return;

    document.getElementById('menuModalTitle').innerHTML = '<i class="fas fa-edit"></i> Edit Dish';
    document.getElementById('item_id').value = item.id;
    document.getElementById('item_name').value = item.name;
    document.getElementById('item_price').value = item.price;
    document.getElementById('item_category').value = item.category;
    document.getElementById('item_prep').value = item.prep_time || '15-20 mins';
    document.getElementById('item_rating').value = item.rating || 4.8;
    document.getElementById('item_image').value = item.image;
    document.getElementById('item_description').value = item.description;
    document.getElementById('item_veg').checked = !!item.is_veg;
    document.getElementById('item_spicy').checked = !!item.is_spicy;
    document.getElementById('item_featured').checked = !!item.is_featured;

    previewMenuImg(item.image);
    openModal('menuItemModal');
}

function previewMenuImg(url) {
    const preview = document.getElementById('itemImgPreview');
    if (url && url.trim()) {
        preview.src = url;
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

async function saveMenuItem() {
    const id = document.getElementById('item_id').value;
    const name = document.getElementById('item_name').value.trim();
    const price = parseFloat(document.getElementById('item_price').value);
    const category = document.getElementById('item_category').value;
    const prep_time = document.getElementById('item_prep').value.trim();
    const rating = parseFloat(document.getElementById('item_rating').value) || 4.8;
    const image = document.getElementById('item_image').value.trim();
    const description = document.getElementById('item_description').value.trim();
    const is_veg = document.getElementById('item_veg').checked;
    const is_spicy = document.getElementById('item_spicy').checked;
    const is_featured = document.getElementById('item_featured').checked;

    if (!name || isNaN(price) || price <= 0) {
        adminToast('Please provide a valid dish name and price.', 'error');
        return;
    }

    const payload = { name, price, category, prep_time, rating, image, description, is_veg, is_spicy, is_featured };
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/admin/menu/${id}` : '/api/admin/menu';

    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            adminToast(id ? 'Dish updated successfully!' : 'New dish added to menu!', 'success');
            closeModal('menuItemModal');
            await fetchMenu();
            await fetchStats();
        } else {
            adminToast(data.error || 'Failed to save dish', 'error');
        }
    } catch(e) {
        adminToast('Error saving menu item', 'error');
    }
}

async function deleteMenuItem(id, name) {
    if (!confirm(`Are you sure you want to permanently delete "${name}" from the menu?`)) return;
    try {
        const res = await fetch(`/api/admin/menu/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            adminToast(`"${name}" deleted!`, 'success');
            await fetchMenu();
            await fetchStats();
        }
    } catch(e) {
        adminToast('Failed to delete item', 'error');
    }
}

// ── Table Reservations ───────────────────────────────────────────────────────
async function fetchReservations() {
    try {
        const res = await fetch('/api/admin/reservations');
        adminState.reservations = await res.json();
        renderReservations();
    } catch(e) {
        console.error('Error fetching reservations:', e);
    }
}

function renderReservations() {
    const tbody = document.getElementById('reservationsBody');
    if (!tbody) return;

    if (!adminState.reservations.length) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:#94a3b8">No table bookings yet</td></tr>';
        return;
    }

    tbody.innerHTML = adminState.reservations.map(r => `
        <tr>
            <td><strong>#${r.id}</strong></td>
            <td><strong>${escapeHtml(r.customer_name)}</strong></td>
            <td>
                <small>${escapeHtml(r.customer_phone)}</small><br>
                <small style="color:#94a3b8">${escapeHtml(r.customer_email)}</small>
            </td>
            <td><strong>${r.guests} Guests</strong></td>
            <td>
                <strong>${r.reservation_date}</strong><br>
                <small style="color:#64748b">${r.reservation_time}</small>
            </td>
            <td><small>${escapeHtml(r.table_type || 'Standard')}</small></td>
            <td><small><em>${escapeHtml(r.special_requests || 'None')}</em></small></td>
            <td><span class="status-badge status-${r.status}">${formatStatus(r.status)}</span></td>
            <td>
                <select class="status-select" onchange="updateReservationStatus(${r.id}, this.value)">
                    <option value="confirmed" ${r.status==='confirmed'?'selected':''}>Confirmed</option>
                    <option value="pending" ${r.status==='pending'?'selected':''}>Pending</option>
                    <option value="completed" ${r.status==='completed'?'selected':''}>Completed</option>
                    <option value="cancelled" ${r.status==='cancelled'?'selected':''}>Cancelled</option>
                </select>
            </td>
        </tr>
    `).join('');
}

async function updateReservationStatus(id, newStatus) {
    try {
        const res = await fetch(`/api/admin/reservations/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            adminToast(`Reservation #${id} updated!`, 'success');
            await fetchReservations();
            await fetchStats();
        }
    } catch(e) {
        adminToast('Failed to update reservation', 'error');
    }
}

// ── Contact Messages ─────────────────────────────────────────────────────────
async function fetchMessages() {
    try {
        const res = await fetch('/api/admin/messages');
        adminState.messages = await res.json();
        renderMessages();
    } catch(e) {
        console.error('Error fetching messages:', e);
    }
}

function renderMessages() {
    const tbody = document.getElementById('messagesBody');
    if (!tbody) return;

    if (!adminState.messages.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#94a3b8">No messages received yet</td></tr>';
        return;
    }

    tbody.innerHTML = adminState.messages.map(m => `
        <tr>
            <td><strong>${escapeHtml(m.name)}</strong></td>
            <td><small>${escapeHtml(m.email)}</small></td>
            <td><strong>${escapeHtml(m.subject || 'General Inquiry')}</strong></td>
            <td style="max-width:320px">${escapeHtml(m.message)}</td>
            <td><small>${m.created_at}</small></td>
            <td><span class="status-badge status-${m.status}">${m.status}</span></td>
            <td>
                ${m.status === 'unread' ? `
                    <button class="btn-action-icon" style="color:#10b981" onclick="markMessageStatus(${m.id}, 'resolved')" title="Mark Resolved">
                        <i class="fas fa-check"></i>
                    </button>
                ` : ''}
                <button class="btn-action-icon delete" onclick="deleteMessage(${m.id})" title="Delete"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>
    `).join('');
}

async function markMessageStatus(id, status) {
    try {
        const res = await fetch(`/api/admin/messages/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (data.success) {
            adminToast('Message resolved!', 'success');
            await fetchMessages();
            await fetchStats();
        }
    } catch(e) {
        adminToast('Failed to update message', 'error');
    }
}

async function deleteMessage(id) {
    if (!confirm('Delete this inquiry message?')) return;
    try {
        const res = await fetch(`/api/admin/messages/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            adminToast('Message removed', 'success');
            await fetchMessages();
            await fetchStats();
        }
    } catch(e) {
        adminToast('Failed to delete message', 'error');
    }
}

// ── Customer Directory ───────────────────────────────────────────────────────
async function fetchUsers() {
    try {
        const res = await fetch('/api/admin/users');
        adminState.users = await res.json();
        renderUsers();
    } catch(e) {
        console.error('Error fetching users:', e);
    }
}

function renderUsers() {
    const tbody = document.getElementById('usersBody');
    if (!tbody) return;

    tbody.innerHTML = adminState.users.map(u => `
        <tr>
            <td><strong>#${u.id}</strong></td>
            <td><strong>${escapeHtml(u.full_name)}</strong></td>
            <td>${escapeHtml(u.email)}</td>
            <td><small>${escapeHtml(u.phone || 'N/A')}</small></td>
            <td>
                <span class="status-badge ${u.role === 'admin' ? 'status-confirmed' : 'status-delivered'}">
                    ${u.role === 'admin' ? '🛡️ Admin' : '👤 Customer'}
                </span>
            </td>
            <td><strong>${u.order_count || 0}</strong></td>
            <td><strong>$${parseFloat(u.total_spent || 0).toFixed(2)}</strong></td>
            <td><small>${u.created_at}</small></td>
        </tr>
    `).join('');
}

// ── Helper Utilities ─────────────────────────────────────────────────────────
function formatStatus(status) {
    if (!status) return '';
    return status.replace(/_/g, ' ');
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ── Initialization ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadAllAdminData();

    // Nav items
    document.querySelectorAll('.admin-nav-item').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Mobile sidebar toggle
    document.getElementById('sidebarToggle')?.addEventListener('click', () => {
        document.getElementById('adminSidebar')?.classList.toggle('open');
    });

    // Order status filter pills
    document.querySelectorAll('#orderStatusFilters .pill').forEach(pill => {
        pill.addEventListener('click', function() {
            document.querySelectorAll('#orderStatusFilters .pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            adminState.orderStatusFilter = this.dataset.status;
            renderMasterOrders();
        });
    });

    // Order search
    document.getElementById('orderSearchInput')?.addEventListener('input', () => {
        renderMasterOrders();
    });

    // Menu category filter pills
    document.querySelectorAll('#menuCategoryFilters .pill').forEach(pill => {
        pill.addEventListener('click', function() {
            document.querySelectorAll('#menuCategoryFilters .pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            adminState.menuCatFilter = this.dataset.cat;
            renderMenuMaster();
        });
    });

    // Menu search
    document.getElementById('menuSearchInput')?.addEventListener('input', () => {
        renderMenuMaster();
    });

    // Close modal on outside click
    window.addEventListener('click', e => {
        ['menuItemModal', 'adminOrderModal'].forEach(id => {
            const el = document.getElementById(id);
            if (el && e.target === el) el.classList.remove('open');
        });
    });
});
