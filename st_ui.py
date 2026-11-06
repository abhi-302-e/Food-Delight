"""
Streamlit Cloud Interface for Foodie Delight.
Enables live interactive ordering, menu browsing, reservations,
and admin management directly when deployed on Streamlit Cloud!
"""
import sqlite3
import os
from datetime import datetime

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def render_streamlit_interface(db_path):
    import streamlit as st

    st.set_page_config(
        page_title="Foodie Delight – Gourmet Dining",
        page_icon="🍔",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state for cart
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    if "coupon" not in st.session_state:
        st.session_state.coupon = None
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    # Custom Restaurant Header Styling
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #ff5722, #ff7043);
            color: white;
            padding: 24px 30px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 8px 24px rgba(255, 87, 34, 0.25);
        }
        .main-header h1 { color: white !important; margin: 0; font-size: 2.2rem; }
        .main-header p { color: #fff3f0; margin: 4px 0 0 0; font-size: 1.05rem; }
        .dish-card {
            background: white;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 16px;
        }
        .badge-pill {
            background: #fff3f0;
            color: #ff5722;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar Navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3075/3075977.png", width=64)
        st.title("Foodie Delight")
        st.caption("Gourmet Kitchen & Express Delivery")
        st.divider()

        cart_count = sum(st.session_state.cart.values())
        nav_options = [
            "🏠 Home & Specials",
            f"🍕 Explore Menu",
            f"🛒 My Cart ({cart_count})",
            "📦 Track Orders",
            "📅 Book a Table",
            "🛡️ Admin Operations",
            "💬 Contact & Inquiries"
        ]
        page = st.radio("Navigate", nav_options)
        st.divider()
        st.info("🔥 **Promo Code:** Use `WELCOME20` at checkout for 20% off!")

    # Top Brand Header Banner
    st.markdown("""
        <div class="main-header">
            <h1>🍽️ Foodie Delight</h1>
            <p>Handcrafted wood-fired pizzas, prime wagyu burgers, and artisan pastas made fresh to order.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db(db_path)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. HOME & SPECIALS
    # ─────────────────────────────────────────────────────────────────────────
    if "🏠 Home" in page:
        st.subheader("🔥 Chef's Signature Specials")
        st.write("Handcrafted dishes prepared with farm-fresh organic ingredients.")

        featured = conn.execute("SELECT * FROM menu_items WHERE is_featured=1 AND available=1 LIMIT 6").fetchall()
        cols = st.columns(3)
        for idx, item in enumerate(featured):
            with cols[idx % 3]:
                st.image(item["image"], use_container_width=True)
                st.markdown(f"**{item['name']}**")
                st.caption(item["description"])
                badges = []
                if item["is_veg"]: badges.append("🌱 Veg")
                if item["is_spicy"]: badges.append("🌶️ Spicy")
                badges.append(f"⏱️ {item['prep_time']}")
                badges.append(f"⭐ {item['rating']}")
                st.write(" · ".join(badges))
                st.markdown(f"### ${item['price']:.2f}")

                col_btn, col_info = st.columns([1, 1])
                with col_btn:
                    if st.button("Add to Cart", key=f"feat_add_{item['id']}"):
                        st.session_state.cart[item["id"]] = st.session_state.cart.get(item["id"], 0) + 1
                        st.success(f"Added {item['name']}!")
                        st.rerun()

        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("⚡ Delivery Speed", "25-35 mins")
        col2.metric("🍕 Artisan Dishes", "33+ Varieties")
        col3.metric("⭐ Customer Rating", "4.9 / 5.0")
        col4.metric("🌿 Fresh Produce", "100% Organic")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. EXPLORE MENU
    # ─────────────────────────────────────────────────────────────────────────
    elif "🍕 Explore Menu" in page:
        st.subheader("Explore Our Full Culinary Menu")

        col_search, col_cat, col_diet = st.columns([2, 1, 1])
        with col_search:
            search_query = st.text_input("🔍 Search dishes or ingredients", placeholder="e.g. Truffle, Pepperoni, Alfredo...")
        with col_cat:
            cat_filter = st.selectbox("Category", ["All", "pizza", "burger", "pasta", "sandwich", "starters", "desserts"])
        with col_diet:
            diet_filter = st.selectbox("Dietary", ["All", "Vegetarian 🌱", "Spicy 🌶️", "Chef's Special ⭐"])

        query = "SELECT * FROM menu_items WHERE available=1"
        params = []
        if cat_filter != "All":
            query += " AND category=?"
            params.append(cat_filter)
        if diet_filter == "Vegetarian 🌱":
            query += " AND is_veg=1"
        elif diet_filter == "Spicy 🌶️":
            query += " AND is_spicy=1"
        elif diet_filter == "Chef's Special ⭐":
            query += " AND is_featured=1"
        if search_query:
            query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
            params.extend([f"%{search_query.lower()}%", f"%{search_query.lower()}%"])

        query += " ORDER BY is_featured DESC, id ASC"
        items = conn.execute(query, params).fetchall()

        st.write(f"Showing **{len(items)}** delicious dishes:")
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                st.image(item["image"], use_container_width=True)
                st.markdown(f"**{item['name']}**")
                st.caption(item["description"])
                st.write(f"🏷️ `{item['category']}` · ⭐ {item['rating']} · ⏱️ {item['prep_time']}")
                st.markdown(f"#### ${item['price']:.2f}")

                current_qty = st.session_state.cart.get(item["id"], 0)
                btn_label = f"Add to Cart ({current_qty})" if current_qty > 0 else "Add to Cart"
                if st.button(btn_label, key=f"menu_add_{item['id']}"):
                    st.session_state.cart[item["id"]] = current_qty + 1
                    st.toast(f"Added {item['name']} to cart!")
                    st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # 3. CART & CHECKOUT
    # ─────────────────────────────────────────────────────────────────────────
    elif "🛒 My Cart" in page:
        st.subheader("Your Food Cart & Delivery Checkout")

        if not st.session_state.cart or sum(st.session_state.cart.values()) == 0:
            st.info("🛒 Your cart is currently empty. Head over to **Explore Menu** and pick your favorite food!")
        else:
            cart_item_ids = list(st.session_state.cart.keys())
            placeholders = ",".join("?" for _ in cart_item_ids)
            db_items = conn.execute(f"SELECT * FROM menu_items WHERE id IN ({placeholders})", cart_item_ids).fetchall()
            item_map = {item["id"]: item for item in db_items}

            subtotal = 0.0
            st.markdown("### Cart Items")
            for item_id, qty in list(st.session_state.cart.items()):
                if qty <= 0 or item_id not in item_map:
                    continue
                item = item_map[item_id]
                item_total = item["price"] * qty
                subtotal += item_total

                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(f"**{item['name']}** (${item['price']:.2f} each)")
                c2.write(f"Qty: **{qty}**")
                c3.write(f"**${item_total:.2f}**")
                with c4:
                    if st.button("➖", key=f"minus_{item_id}"):
                        if qty == 1:
                            del st.session_state.cart[item_id]
                        else:
                            st.session_state.cart[item_id] -= 1
                        st.rerun()
                    if st.button("➕", key=f"plus_{item_id}"):
                        st.session_state.cart[item_id] += 1
                        st.rerun()

            st.divider()

            # Coupon code
            c_coup1, c_coup2 = st.columns([3, 1])
            with c_coup1:
                entered_coupon = st.text_input("Promo Code", placeholder="e.g. WELCOME20", value=st.session_state.coupon or "")
            with c_coup2:
                if st.button("Apply Code"):
                    if entered_coupon.upper() == "WELCOME20":
                        st.session_state.coupon = "WELCOME20"
                        st.success("20% Discount Applied!")
                        st.rerun()
                    elif entered_coupon.upper() == "FOODIE10":
                        st.session_state.coupon = "FOODIE10"
                        st.success("$10 Discount Applied!")
                        st.rerun()
                    else:
                        st.error("Invalid coupon code.")

            discount = 0.0
            if st.session_state.coupon == "WELCOME20":
                discount = round(subtotal * 0.20, 2)
            elif st.session_state.coupon == "FOODIE10":
                discount = min(subtotal, 10.0)

            final_total = max(0.0, subtotal - discount)

            st.write(f"Subtotal: **${subtotal:.2f}**")
            if discount > 0:
                st.write(f"Promo Discount: **-${discount:.2f}** ({st.session_state.coupon})")
            st.write("Delivery Fee: **FREE**")
            st.markdown(f"## Total Due: ${final_total:.2f}")

            st.divider()
            st.subheader("Delivery Information")
            with st.form("checkout_form"):
                cust_name = st.text_input("Full Name *", placeholder="John Doe")
                cust_email = st.text_input("Email Address *", placeholder="you@example.com")
                cust_phone = st.text_input("Phone Number *", placeholder="+1 234 567 8900")
                cust_addr = st.text_area("Delivery Address *", placeholder="Apartment / Suite, Street Address, City")
                cust_notes = st.text_input("Kitchen / Delivery Notes", placeholder="e.g. Please ring doorbell")
                cust_pay = st.selectbox("Payment Method", ["Cash on Delivery", "Credit / Debit Card (On Delivery)", "UPI / QR Code"])
                submit_order = st.form_submit_button("Confirm & Place Order")

                if submit_order:
                    if not cust_name or not cust_email or not cust_addr or not cust_phone:
                        st.error("Please fill in all required customer details.")
                    else:
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with conn:
                            cursor = conn.execute(
                                """INSERT INTO orders (user_id, customer_name, customer_email, customer_phone, address, total, status, payment_method, notes, created_at)
                                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (1, cust_name, cust_email, cust_phone, cust_addr, final_total, "pending", cust_pay, cust_notes, now_str)
                            )
                            order_id = cursor.lastrowid
                            for item_id, qty in st.session_state.cart.items():
                                if qty > 0 and item_id in item_map:
                                    it = item_map[item_id]
                                    conn.execute(
                                        """INSERT INTO order_items (order_id, menu_item_id, name, price, quantity)
                                           VALUES (?,?,?,?,?)""",
                                        (order_id, item_id, it["name"], it["price"], qty)
                                    )
                        st.session_state.cart = {}
                        st.session_state.coupon = None
                        st.balloons()
                        st.success(f"🎉 Order #{order_id} placed successfully! Our chefs are preparing your food.")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. TRACK ORDERS
    # ─────────────────────────────────────────────────────────────────────────
    elif "📦 Track Orders" in page:
        st.subheader("Live Order Tracking & History")
        orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20").fetchall()
        if not orders:
            st.info("No orders placed yet.")
        else:
            for o in orders:
                with st.expander(f"Order #{o['id']} · ${o['total']:.2f} · Status: {o['status'].upper()} ({o['created_at']})", expanded=True):
                    col_info, col_stat = st.columns([2, 1])
                    with col_info:
                        st.write(f"**Customer:** {o['customer_name']} ({o['customer_email']})")
                        st.write(f"**Phone:** {o['customer_phone']}")
                        st.write(f"**Delivery Address:** {o['address']}")
                        st.write(f"**Payment:** {o['payment_method']}")
                        if o['notes']: st.write(f"*Notes:* {o['notes']}")
                    with col_stat:
                        status_emojis = {
                            "pending": "⏳ Pending (Received)",
                            "confirmed": "✅ Confirmed",
                            "preparing": "🍳 Cooking in Kitchen",
                            "out_for_delivery": "🛵 Out for Delivery",
                            "delivered": "🎉 Delivered",
                            "cancelled": "❌ Cancelled"
                        }
                        st.info(f"**Status:** {status_emojis.get(o['status'], o['status'])}")

                    items = conn.execute("SELECT * FROM order_items WHERE order_id=?", (o['id'],)).fetchall()
                    if items:
                        st.markdown("**Items:**")
                        for it in items:
                            st.write(f"- {it['name']} × {it['quantity']} (${it['price']:.2f} each)")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. BOOK A TABLE
    # ─────────────────────────────────────────────────────────────────────────
    elif "📅 Book a Table" in page:
        st.subheader("Reserve Your Dine-In Table")
        st.write("Join us for an unforgettable culinary experience.")

        with st.form("reservation_form"):
            r_name = st.text_input("Full Name *", placeholder="Jane Doe")
            col_e, col_p = st.columns(2)
            with col_e: r_email = st.text_input("Email Address *", placeholder="jane@example.com")
            with col_p: r_phone = st.text_input("Phone Number *", placeholder="+1 234 567 8900")

            col_g, col_d, col_t = st.columns(3)
            with col_g: r_guests = st.selectbox("Number of Guests", [1, 2, 3, 4, 5, 6, 8, 10], index=1)
            with col_d: r_date = st.date_input("Date")
            with col_t: r_time = st.selectbox("Preferred Time", ["12:00 PM", "1:00 PM", "2:00 PM", "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM"], index=4)

            col_area, col_occ = st.columns(2)
            with col_area: r_area = st.selectbox("Seating Area", ["Indoor Main Dining Room", "Romantic Window Booth", "Outdoor Garden Patio", "Chef's Open Counter"])
            with col_occ: r_occ = st.selectbox("Occasion", ["Casual Dining", "Birthday Celebration 🎂", "Anniversary 🥂", "Date Night ✨", "Business Dinner 👔"])

            r_requests = st.text_input("Special Requests", placeholder="e.g. High chair requested, anniversary dessert")
            submit_res = st.form_submit_button("Confirm Table Reservation")

            if submit_res:
                if not r_name or not r_email or not r_phone:
                    st.error("Please fill in your name, email, and phone number.")
                else:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with conn:
                        cursor = conn.execute(
                            """INSERT INTO reservations (customer_name, customer_email, customer_phone, guests, reservation_date, reservation_time, table_type, special_requests, status, created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (r_name, r_email, r_phone, r_guests, str(r_date), r_time, r_area, f"{r_occ} - {r_requests}", "confirmed", now_str)
                        )
                    st.balloons()
                    st.success(f"🎉 Table reserved for {r_guests} guests on {r_date} at {r_time}! Booking #{cursor.lastrowid}")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. ADMIN OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────
    elif "🛡️ Admin Operations" in page:
        st.subheader("Restaurant Admin Console")

        if not st.session_state.admin_logged_in:
            st.write("Please enter your admin credentials to access operations:")
            with st.form("admin_login"):
                admin_pw = st.text_input("Admin Password", type="password", placeholder="Enter admin password (admin123)")
                if st.form_submit_button("Sign In as Admin"):
                    if admin_pw == "admin123":
                        st.session_state.admin_logged_in = True
                        st.success("Admin authorized!")
                        st.rerun()
                    else:
                        st.error("Invalid password. Default demo password is `admin123`")
        else:
            if st.button("Logout Admin"):
                st.session_state.admin_logged_in = False
                st.rerun()

            # KPI Metrics
            rev = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'cancelled'").fetchone()[0]
            tot_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            pend_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]
            tot_items = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
            tot_res = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("💰 Total Revenue", f"${rev:.2f}")
            m2.metric("🛍️ Total Orders", tot_orders)
            m3.metric("⏳ Pending Orders", pend_orders)
            m4.metric("🍕 Active Dishes", tot_items)
            m5.metric("📅 Reservations", tot_res)

            admin_tab = st.selectbox("Manage Section", ["📦 Customer Orders", "🍕 Menu Catalog", "📅 Table Bookings", "💬 Customer Inquiries"])

            if admin_tab == "📦 Customer Orders":
                st.markdown("### Live Orders Management")
                all_orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
                for o in all_orders:
                    c1, c2, c3 = st.columns([3, 2, 2])
                    c1.write(f"**Order #{o['id']}** · {o['customer_name']} (${o['total']:.2f})")
                    c1.caption(f"{o['customer_phone']} · {o['address']}")
                    new_status = c2.selectbox(
                        "Status",
                        ["pending", "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled"],
                        index=["pending", "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled"].index(o['status']),
                        key=f"status_sel_{o['id']}"
                    )
                    if new_status != o['status']:
                        with conn:
                            conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, o['id']))
                        st.toast(f"Order #{o['id']} updated to {new_status}!")
                        st.rerun()

            elif admin_tab == "🍕 Menu Catalog":
                st.markdown("### Menu Items Management")
                with st.expander("➕ Add New Dish to Menu"):
                    with st.form("add_dish_form"):
                        d_name = st.text_input("Dish Name")
                        d_price = st.number_input("Price ($)", min_value=1.0, value=14.99, step=0.5)
                        d_cat = st.selectbox("Category", ["pizza", "burger", "pasta", "sandwich", "starters", "desserts"])
                        d_img = st.text_input("Image URL", value="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=700&q=80")
                        d_desc = st.text_area("Description")
                        d_veg = st.checkbox("Vegetarian 🌱")
                        d_spicy = st.checkbox("Spicy 🌶️")
                        d_feat = st.checkbox("Chef's Special ⭐")
                        if st.form_submit_button("Add Dish"):
                            with conn:
                                conn.execute(
                                    """INSERT INTO menu_items (name, price, category, image, description, available, is_veg, is_spicy, is_featured, prep_time, rating)
                                       VALUES (?,?,?,?,?,1,?,?,?, '15-20 mins', 4.9)""",
                                    (d_name, d_price, d_cat, d_img, d_desc, 1 if d_veg else 0, 1 if d_spicy else 0, 1 if d_feat else 0)
                                )
                            st.success("New dish added to menu!")
                            st.rerun()

                all_items = conn.execute("SELECT * FROM menu_items ORDER BY id DESC").fetchall()
                for it in all_items:
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{it['name']}** (${it['price']:.2f}) · `{it['category']}`")
                    avail = c2.checkbox("In Stock", value=bool(it['available']), key=f"avail_{it['id']}")
                    if avail != bool(it['available']):
                        with conn:
                            conn.execute("UPDATE menu_items SET available=? WHERE id=?", (1 if avail else 0, it['id']))
                        st.rerun()
                    if c3.button("Delete", key=f"del_{it['id']}"):
                        with conn:
                            conn.execute("DELETE FROM menu_items WHERE id=?", (it['id'],))
                        st.rerun()

            elif admin_tab == "📅 Table Bookings":
                st.markdown("### Table Bookings")
                res = conn.execute("SELECT * FROM reservations ORDER BY reservation_date DESC, reservation_time DESC").fetchall()
                for r in res:
                    st.write(f"**Booking #{r['id']}** · {r['customer_name']} ({r['guests']} Guests) on **{r['reservation_date']} at {r['reservation_time']}** · *{r['table_type']}*")
                    st.caption(f"Phone: {r['customer_phone']} · Email: {r['customer_email']} · Requests: {r['special_requests']}")
                    st.divider()

            elif admin_tab == "💬 Customer Inquiries":
                st.markdown("### Customer Messages")
                msgs = conn.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()
                if not msgs:
                    st.info("No messages received yet.")
                else:
                    for m in msgs:
                        st.write(f"**From:** {m['name']} ({m['email']}) · *{m['subject']}* ({m['created_at']})")
                        st.write(m['message'])
                        st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # 7. CONTACT & INQUIRIES
    # ─────────────────────────────────────────────────────────────────────────
    elif "💬 Contact" in page:
        st.subheader("Contact Our Hospitality Team")
        with st.form("contact_form"):
            c_name = st.text_input("Your Name *")
            c_email = st.text_input("Your Email *")
            c_subj = st.selectbox("Subject", ["General Inquiry", "Private Events & Catering", "Feedback", "Dietary Inquiries"])
            c_msg = st.text_area("Your Message *")
            if st.form_submit_button("Send Message"):
                if not c_name or not c_email or not c_msg:
                    st.error("Please fill in all fields.")
                else:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with conn:
                        conn.execute(
                            "INSERT INTO contact_messages (name, email, subject, message, status, created_at) VALUES (?,?,?,?,?,?)",
                            (c_name, c_email, c_subj, c_msg, "unread", now_str)
                        )
                    st.success("Thank you! Your message has been sent to our team.")
