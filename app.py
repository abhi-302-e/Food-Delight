from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'foodiedelight_secret_key_2025_upgraded'

DB_PATH = os.path.join(os.path.dirname(__file__), 'foodie_delight.db')

# ─── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        # Base tables
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                address TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'customer',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                image TEXT NOT NULL,
                description TEXT NOT NULL,
                available INTEGER DEFAULT 1,
                is_veg INTEGER DEFAULT 0,
                is_spicy INTEGER DEFAULT 0,
                is_featured INTEGER DEFAULT 0,
                prep_time TEXT DEFAULT '20 mins',
                rating REAL DEFAULT 4.8
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT,
                address TEXT,
                total REAL NOT NULL,
                status TEXT DEFAULT "pending",
                payment_method TEXT DEFAULT "Cash on Delivery",
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            );
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                guests INTEGER NOT NULL,
                reservation_date TEXT NOT NULL,
                reservation_time TEXT NOT NULL,
                table_type TEXT DEFAULT 'Standard Indoor',
                special_requests TEXT,
                status TEXT DEFAULT 'confirmed',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT DEFAULT 'General Inquiry',
                message TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TEXT NOT NULL
            );
        ''')

        # Auto-migration: ensure newly added columns exist in older tables
        # Check users table columns
        user_cols = [r[1] for r in db.execute('PRAGMA table_info(users)').fetchall()]
        if 'role' not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer'")

        # Check menu_items table columns
        menu_cols = [r[1] for r in db.execute('PRAGMA table_info(menu_items)').fetchall()]
        if 'is_veg' not in menu_cols:
            db.execute("ALTER TABLE menu_items ADD COLUMN is_veg INTEGER DEFAULT 0")
        if 'is_spicy' not in menu_cols:
            db.execute("ALTER TABLE menu_items ADD COLUMN is_spicy INTEGER DEFAULT 0")
        if 'is_featured' not in menu_cols:
            db.execute("ALTER TABLE menu_items ADD COLUMN is_featured INTEGER DEFAULT 0")
        if 'prep_time' not in menu_cols:
            db.execute("ALTER TABLE menu_items ADD COLUMN prep_time TEXT DEFAULT '20 mins'")
        if 'rating' not in menu_cols:
            db.execute("ALTER TABLE menu_items ADD COLUMN rating REAL DEFAULT 4.8")

        # Check orders table columns
        order_cols = [r[1] for r in db.execute('PRAGMA table_info(orders)').fetchall()]
        if 'payment_method' not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'Cash on Delivery'")
        if 'notes' not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN notes TEXT")

        # Check contact_messages table columns
        contact_cols = [r[1] for r in db.execute('PRAGMA table_info(contact_messages)').fetchall()]
        if 'subject' not in contact_cols:
            db.execute("ALTER TABLE contact_messages ADD COLUMN subject TEXT DEFAULT 'General Inquiry'")
        if 'status' not in contact_cols:
            db.execute("ALTER TABLE contact_messages ADD COLUMN status TEXT DEFAULT 'unread'")

        # Seed master admin if not present
        admin_user = db.execute("SELECT id FROM users WHERE email='admin@foodiedelight.com'").fetchone()
        if not admin_user:
            admin_hash = generate_password_hash('admin123')
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.execute(
                "INSERT INTO users (full_name, email, phone, address, password_hash, role, created_at) VALUES (?,?,?,?,?,?,?)",
                ('Master Admin', 'admin@foodiedelight.com', '+1 (800) 555-FOOD', 'Executive Chef Suite 101, Food Delight Plaza', admin_hash, 'admin', now_str)
            )

        # Seed rich 30+ item menu if fewer than 15 items exist
        item_count = db.execute('SELECT COUNT(*) FROM menu_items').fetchone()[0]
        if item_count < 15:
            # Clear old small set or keep and expand
            db.execute('DELETE FROM menu_items')
            expanded_items = [
                # Pizzas
                ('Margherita Di Bufala', 13.99, 'pizza', 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=700&q=80',
                 'San Marzano tomato sauce, fresh buffalo mozzarella, aromatic sweet basil, extra virgin olive oil.', 1, 1, 0, 1, '15-20 mins', 4.9),
                ('Double Pepperoni Rustica', 15.99, 'pizza', 'https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=700&q=80',
                 'Crispy artisan pepperoni cups, aged whole milk mozzarella, rich marinara reduction, hot honey drizzle.', 1, 0, 1, 1, '18-22 mins', 4.9),
                ('Truffle & Wild Mushroom Pizza', 17.99, 'pizza', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=700&q=80',
                 'Roasted cremini and shiitake mushrooms, white truffle cream, fontina cheese, fresh thyme, sea salt flakes.', 1, 1, 0, 1, '20-25 mins', 4.8),
                ('Smokey BBQ Chicken Pizza', 16.49, 'pizza', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=700&q=80',
                 'Wood-fired grilled chicken, tangy smokey BBQ sauce, caramelized red onions, smoked gouda, fresh cilantro.', 1, 0, 0, 0, '18-20 mins', 4.7),
                ('Fiery Diavola Pizza', 16.99, 'pizza', 'https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?auto=format&fit=crop&w=700&q=80',
                 'Spicy Calabrian salami, crushed red pepper flakes, fresh jalapeño rings, mozzarella, spicy chili oil.', 1, 0, 1, 0, '15-20 mins', 4.8),
                ('Paneer Tikka Supreme', 14.99, 'pizza', 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=700&q=80',
                 'Tandoori spiced cottage cheese cubes, charred bell peppers, red onions, fresh coriander, mint yogurt swirl.', 1, 1, 1, 0, '18-22 mins', 4.7),

                # Burgers
                ('Classic Angus Cheeseburger', 11.99, 'burger', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=700&q=80',
                 'Prime Angus beef patty, melted aged cheddar, crisp butterhead lettuce, ripe beefsteak tomato, house special secret burger sauce.', 1, 0, 0, 1, '12-15 mins', 4.9),
                ('Crispy Buttermilk Chicken Burger', 12.99, 'burger', 'https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?auto=format&fit=crop&w=700&q=80',
                 'Crispy double-dredged buttermilk chicken breast, spicy honey glaze, creamy cabbage slaw, dill pickles on toasted brioche.', 1, 0, 1, 1, '15-18 mins', 4.9),
                ('Double Truffle Wagyu Smash', 16.99, 'burger', 'https://images.unsplash.com/photo-1586190848861-99aa4a171e90?auto=format&fit=crop&w=700&q=80',
                 'Two smashed American Wagyu patties, melted Swiss gruyère, black truffle mayo, caramelized balsamic onions.', 1, 0, 0, 1, '15-20 mins', 5.0),
                ('Fiery Bacon Jalapeño Burger', 13.99, 'burger', 'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=700&q=80',
                 'Smoked Applewood bacon, crispy grilled patty, pepper jack cheese, charred jalapeños, smoked chipotle aioli.', 1, 0, 1, 0, '14-16 mins', 4.8),
                ('Gourmet Portobello Burger', 12.49, 'burger', 'https://images.unsplash.com/photo-1520072959219-c595dc870360?auto=format&fit=crop&w=700&q=80',
                 'Balsamic marinated grilled portobello cap, garlic-herb goat cheese, baby arugula, sun-dried tomato spread.', 1, 1, 0, 0, '12-15 mins', 4.6),
                ('Garden Harvest Black Bean Burger', 10.99, 'burger', 'https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?auto=format&fit=crop&w=700&q=80',
                 'House-crafted spiced quinoa and black bean patty, fresh avocado mash, crisp romaine, dairy-free chipotle crema.', 1, 1, 0, 0, '12-15 mins', 4.7),

                # Sandwiches
                ('Grand Triple-Decker Club Sandwich', 10.99, 'sandwich', 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=700&q=80',
                 'Layers of slow-roasted turkey breast, crispy bacon strips, aged cheddar, crisp iceberg, juicy tomato, herb dijon aioli on toasted brioche.', 1, 0, 0, 1, '10-12 mins', 4.8),
                ('Avocado & Burrata Sourdough', 11.49, 'sandwich', 'https://images.unsplash.com/photo-1603064752734-4c48eff53d05?auto=format&fit=crop&w=700&q=80',
                 'Artisan toasted sourdough, hand-torn creamy Italian burrata, crushed Hass avocado, cherry heirloom tomatoes, aged balsamic reduction.', 1, 1, 0, 1, '8-10 mins', 4.9),
                ('Grilled Chicken Pesto Panini', 12.49, 'sandwich', 'https://images.unsplash.com/photo-1509722747041-616f39b57569?auto=format&fit=crop&w=700&q=80',
                 'Marinated chicken breast, fragrant Genovese basil pesto, melted fresh mozzarella, sun-ripened tomatoes on pressed ciabatta.', 1, 0, 0, 0, '12-14 mins', 4.8),
                ('Philly Cheesesteak Melt', 13.99, 'sandwich', 'https://images.unsplash.com/photo-1553909489-cd47e0907980?auto=format&fit=crop&w=700&q=80',
                 'Tender shaved ribeye steak, sautéed bell peppers and sweet Spanish onions, melted provolone on warm toasted hoagie.', 1, 0, 0, 1, '14-16 mins', 4.9),
                ('Smoked Salmon Bagel Deluxe', 12.99, 'sandwich', 'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=700&q=80',
                 'Norwegian smoked salmon, whipped scallion dill cream cheese, capers, thinly sliced cucumber, red onion on toasted sesame bagel.', 1, 0, 0, 0, '8-10 mins', 4.8),

                # Pastas & Mains
                ('Handcrafted Fettuccine Alfredo', 14.99, 'pasta', 'https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=700&q=80',
                 'Fresh silky egg fettuccine tossed in 24-month Parmigiano-Reggiano cream, European cultured butter, cracked tellicherry pepper.', 1, 1, 0, 1, '15-18 mins', 4.9),
                ('Slow-Cooked Bolognese Tagliatelle', 16.99, 'pasta', 'https://images.unsplash.com/photo-1621996346565-e3d5d6281290?auto=format&fit=crop&w=700&q=80',
                 'Authentic 6-hour slow braised beef, pork, and San Marzano tomato ragù, rosemary, wide ribbon tagliatelle, shaved pecorino.', 1, 0, 0, 1, '18-20 mins', 5.0),
                ('Penne Alla Vodka with Crispy Pancetta', 15.99, 'pasta', 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=700&q=80',
                 'Bronze-die penne enveloped in a velvety tomato cream sauce with a touch of vodka, crispy cured pancetta, fresh basil chiffonade.', 1, 0, 1, 0, '15-18 mins', 4.8),
                ('Wild Mushroom Truffle Risotto', 17.49, 'pasta', 'https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=700&q=80',
                 'Creamy Italian Carnaroli rice, pan-sautéed wild chanterelles and porcini, crisp white wine reduction, shaved black summer truffle.', 1, 1, 0, 1, '20-25 mins', 4.9),
                ('Pan-Seared Lemon Herb Salmon', 19.99, 'pasta', 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=700&q=80',
                 'Crispy-skinned Atlantic salmon fillet, zesty garlic herb butter sauce, charred asparagus spears, roasted rosemary baby potatoes.', 1, 0, 0, 1, '20-22 mins', 4.9),

                # Starters & Snacks
                ('Truffle Parmesan Hand-Cut Fries', 7.99, 'starters', 'https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=700&q=80',
                 'Crispy double-cooked potato frites, white truffle oil, freshly grated Grana Padano, chopped rosemary, garlic dipping aioli.', 1, 1, 0, 1, '10-12 mins', 4.9),
                ('Crispy Buffalo Wings (8 pcs)', 10.99, 'starters', 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=700&q=80',
                 'Jumbo tender wings tossed in classic fiery cayenne glaze, served with crisp celery sticks and house gorgonzola dip.', 1, 0, 1, 1, '14-16 mins', 4.8),
                ('Golden Calamari Fritti', 11.99, 'starters', 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=700&q=80',
                 'Tender squid rings flashed in seasoned flour, served crispy with charred lemon halves and house san marzano marinara.', 1, 0, 0, 0, '10-12 mins', 4.7),
                ('Cheesy Garlic Herb Pull-Apart Bread', 6.99, 'starters', 'https://images.unsplash.com/photo-1619895092538-128341789043?auto=format&fit=crop&w=700&q=80',
                 'Artisan sourdough loaf stuffed with roasted garlic butter, parsley, stringy melted mozzarella, and sharp cheddar.', 1, 1, 0, 0, '10-12 mins', 4.8),
                ('Mediterranean Mezze Platter', 9.99, 'starters', 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=700&q=80',
                 'Velvety chickpea hummus, smoked eggplant dip, marinated kalamata olives, feta chunks, warm zaatar spiced pita wedges.', 1, 1, 0, 0, '8-10 mins', 4.8),

                # Desserts & Beverages
                ('Belgian Molten Chocolate Lava Cake', 8.99, 'desserts', 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=700&q=80',
                 'Warm decadent dark chocolate cake with a flowing molten core, served with Madagascar vanilla bean gelato and strawberry coulis.', 1, 1, 0, 1, '12-15 mins', 5.0),
                ('New York Berry Cheesecake', 7.99, 'desserts', 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=700&q=80',
                 'Rich velvet cream cheese filling on buttered graham cracker crust, topped with fresh blackberries, blueberries, and raspberry drizzle.', 1, 1, 0, 0, 'Ready', 4.9),
                ('Artisanal Coffee Tiramisu', 8.49, 'desserts', 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=700&q=80',
                 'Espresso-dipped savoiardi ladyfingers layered with sweet mascarpone sabayon, dusted with Valrhona bitter cocoa.', 1, 1, 0, 1, 'Ready', 4.9),
                ('Tropical Mango Passionfruit Cooler', 5.99, 'desserts', 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=700&q=80',
                 'Ripe Alphonso mango puree, passionfruit nectar, sparkling soda, fresh garden mint, crushed ice.', 1, 1, 0, 0, '5 mins', 4.8),
                ('Iced Caramel Macchiato', 5.49, 'desserts', 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=700&q=80',
                 'Slow-dripped espresso, silky chilled whole milk, Madagascar vanilla syrup, rich buttery caramel grid drizzle.', 1, 1, 0, 0, '5 mins', 4.7),
                ('Wild Berry Mint Mojito', 5.99, 'desserts', 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=700&q=80',
                 'Muddled wild berries, fresh garden spearmint, Persian lime juice, raw organic cane syrup, chilled mineral soda.', 1, 1, 0, 0, '5 mins', 4.8)
            ]
            db.executemany(
                '''INSERT INTO menu_items (name, price, category, image, description, available, is_veg, is_spicy, is_featured, prep_time, rating)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                expanded_items
            )
        db.commit()

# ─── Auth helpers ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login required', 'login_required': True}), 401
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Admin login required', 'login_required': True}), 401
            return redirect(url_for('login', next=request.path))
        u = current_user()
        if not u or u['role'] != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access denied'}), 403
            return render_template('login.html', error='Admin privileges required. Please login with an admin account.'), 403
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' not in session:
        return None
    with get_db() as db:
        return db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()

# ─── Page Routes ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', user=current_user())

@app.route('/menu')
def menu():
    return render_template('menu.html', user=current_user())

@app.route('/reservations')
def reservations_page():
    return render_template('reservations.html', user=current_user())

@app.route('/about')
def about():
    return render_template('about.html', user=current_user())

@app.route('/contact')
def contact():
    return render_template('contact.html', user=current_user())

@app.route('/orders')
@login_required
def orders_page():
    return render_template('orders.html', user=current_user())

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user())

# ─── Admin Dashboard Page ─────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_page():
    return render_template('admin.html', user=current_user())

# ─── Auth Pages ───────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        u = current_user()
        if u and u['role'] == 'admin':
            return redirect(url_for('admin_page'))
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.get_json() or request.form
        email = str(data.get('email', '')).strip().lower()
        password = str(data.get('password', ''))
        next_url = data.get('next', '')
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']
            target = next_url if next_url and next_url != 'None' else ('/admin' if user['role'] == 'admin' else '/')
            if request.is_json:
                return jsonify({
                    'success': True,
                    'redirect': target,
                    'user': {
                        'id': user['id'],
                        'full_name': user['full_name'],
                        'email': user['email'],
                        'role': user['role']
                    }
                })
            return redirect(target)
        if request.is_json:
            return jsonify({'error': 'Invalid email or password'}), 401
        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html', next=request.args.get('next', ''))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.get_json() or request.form
        full_name = str(data.get('full_name', '')).strip()
        email = str(data.get('email', '')).strip().lower()
        phone = str(data.get('phone', '')).strip()
        address = str(data.get('address', '')).strip()
        password = str(data.get('password', ''))
        confirm = str(data.get('confirm_password', ''))
        errors = []
        if not full_name: errors.append('Full name is required.')
        if not email or '@' not in email: errors.append('Valid email is required.')
        if len(password) < 6: errors.append('Password must be at least 6 characters.')
        if password != confirm: errors.append('Passwords do not match.')
        if not errors:
            with get_db() as db:
                exists = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
                if exists:
                    errors.append('Email is already registered. Please login.')
                else:
                    pw_hash = generate_password_hash(password)
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor = db.execute(
                        'INSERT INTO users (full_name, email, phone, address, password_hash, role, created_at) VALUES (?,?,?,?,?,?,?)',
                        (full_name, email, phone, address, pw_hash, 'customer', created_at)
                    )
                    db.commit()
                    user_id = cursor.lastrowid
                    session['user_id'] = user_id
                    session['user_name'] = full_name
                    session['user_role'] = 'customer'
                    if request.is_json:
                        return jsonify({'success': True, 'user': {'id': user_id, 'full_name': full_name, 'email': email, 'role': 'customer'}})
                    return redirect(url_for('index'))
        if request.is_json:
            return jsonify({'error': errors[0]}), 400
        return render_template('register.html', error=errors[0], form=data)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── API: Auth status ─────────────────────────────────────────────────────────
@app.route('/api/auth/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'logged_in': False})
    u = current_user()
    if not u:
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'user': {
            'id': u['id'],
            'full_name': u['full_name'],
            'email': u['email'],
            'phone': u['phone'],
            'address': u['address'],
            'role': u['role']
        }
    })

# ─── API: Menu ────────────────────────────────────────────────────────────────
@app.route('/api/menu')
def api_menu():
    category = request.args.get('category', 'all').strip()
    search = request.args.get('search', '').strip().lower()
    diet = request.args.get('diet', 'all').strip()
    sort_by = request.args.get('sort', 'default').strip()

    query = 'SELECT * FROM menu_items WHERE available=1'
    params = []

    if category and category != 'all':
        query += ' AND category=?'
        params.append(category)

    if diet == 'veg':
        query += ' AND is_veg=1'
    elif diet == 'spicy':
        query += ' AND is_spicy=1'
    elif diet == 'featured':
        query += ' AND is_featured=1'

    if search:
        query += ' AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(category) LIKE ?)'
        wild = f'%{search}%'
        params.extend([wild, wild, wild])

    if sort_by == 'price_asc':
        query += ' ORDER BY price ASC'
    elif sort_by == 'price_desc':
        query += ' ORDER BY price DESC'
    elif sort_by == 'rating':
        query += ' ORDER BY rating DESC'
    else:
        query += ' ORDER BY is_featured DESC, id ASC'

    with get_db() as db:
        items = db.execute(query, params).fetchall()
    return jsonify([dict(i) for i in items])

@app.route('/api/menu/featured')
def api_featured():
    with get_db() as db:
        items = db.execute('SELECT * FROM menu_items WHERE available=1 AND is_featured=1 LIMIT 6').fetchall()
        if not items:
            items = db.execute('SELECT * FROM menu_items WHERE available=1 LIMIT 6').fetchall()
    return jsonify([dict(i) for i in items])

# ─── API: Coupons ─────────────────────────────────────────────────────────────
@app.route('/api/coupon/validate', methods=['POST'])
def validate_coupon():
    data = request.get_json() or {}
    code = str(data.get('code', '')).strip().upper()
    total = float(data.get('total', 0.0))

    valid_coupons = {
        'WELCOME20': {'percent': 20, 'desc': '20% off your order!'},
        'FOODIE10': {'amount': 10, 'desc': '$10 off your feast!'},
        'TASTY15': {'percent': 15, 'desc': '15% off delicious treat!'},
        'FREESHIP': {'shipping': 0, 'desc': 'Free express shipping!'}
    }

    if code in valid_coupons:
        c = valid_coupons[code]
        discount = 0.0
        if 'percent' in c:
            discount = round(total * (c['percent'] / 100), 2)
        elif 'amount' in c:
            discount = min(total, float(c['amount']))
        return jsonify({'valid': True, 'discount': discount, 'code': code, 'description': c['desc']})
    return jsonify({'valid': False, 'error': 'Invalid coupon code. Try WELCOME20 or FOODIE10!'}), 400

# ─── API: Orders ──────────────────────────────────────────────────────────────
@app.route('/api/orders', methods=['POST'])
@login_required
def place_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    u = current_user()
    phone = str(data.get('customer_phone', u['phone'] or '')).strip()
    address = str(data.get('address', u['address'] or '')).strip()
    payment_method = str(data.get('payment_method', 'Cash on Delivery')).strip()
    notes = str(data.get('notes', '')).strip()
    items = data.get('items', [])
    discount = float(data.get('discount', 0.0))

    if not items:
        return jsonify({'error': 'Your cart is empty'}), 400
    if not address:
        return jsonify({'error': 'Delivery address is required'}), 400

    raw_total = sum(float(i['price']) * int(i['quantity']) for i in items)
    final_total = max(0.0, round(raw_total - discount, 2))
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as db:
        cursor = db.execute(
            '''INSERT INTO orders (user_id, customer_name, customer_email, customer_phone, address, total, status, payment_method, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (u['id'], u['full_name'], u['email'], phone, address, final_total, 'pending', payment_method, notes, created_at)
        )
        order_id = cursor.lastrowid
        for item in items:
            db.execute(
                '''INSERT INTO order_items (order_id, menu_item_id, name, price, quantity)
                   VALUES (?,?,?,?,?)''',
                (order_id, item['id'], item['name'], float(item['price']), int(item['quantity']))
            )
        db.commit()

    return jsonify({'success': True, 'order_id': order_id, 'total': final_total, 'created_at': created_at})

@app.route('/api/orders/<int:order_id>')
@login_required
def get_order(order_id):
    with get_db() as db:
        u = current_user()
        if u['role'] == 'admin':
            order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
        else:
            order = db.execute('SELECT * FROM orders WHERE id=? AND user_id=?', (order_id, u['id'])).fetchone()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        items = db.execute('SELECT * FROM order_items WHERE order_id=?', (order_id,)).fetchall()
    return jsonify({'order': dict(order), 'items': [dict(i) for i in items]})

@app.route('/api/orders')
@login_required
def list_orders():
    with get_db() as db:
        orders = db.execute(
            'SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],)
        ).fetchall()
    return jsonify([dict(o) for o in orders])

# ─── API: Table Reservations ──────────────────────────────────────────────────
@app.route('/api/reservations', methods=['POST'])
def book_reservation():
    data = request.get_json() or {}
    name = str(data.get('customer_name', '')).strip()
    email = str(data.get('customer_email', '')).strip()
    phone = str(data.get('customer_phone', '')).strip()
    guests = int(data.get('guests', 2))
    date = str(data.get('reservation_date', '')).strip()
    time = str(data.get('reservation_time', '')).strip()
    table_type = str(data.get('table_type', 'Standard Indoor')).strip()
    special_requests = str(data.get('special_requests', '')).strip()

    if not name or not email or not phone or not date or not time:
        return jsonify({'error': 'Please fill all required reservation details'}), 400

    user_id = session.get('user_id')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as db:
        cursor = db.execute(
            '''INSERT INTO reservations (user_id, customer_name, customer_email, customer_phone, guests, reservation_date, reservation_time, table_type, special_requests, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (user_id, name, email, phone, guests, date, time, table_type, special_requests, 'confirmed', created_at)
        )
        db.commit()
        booking_id = cursor.lastrowid

    return jsonify({'success': True, 'booking_id': booking_id, 'message': 'Reservation confirmed! We look forward to hosting you.'})

@app.route('/api/reservations/my')
@login_required
def my_reservations():
    with get_db() as db:
        bookings = db.execute('SELECT * FROM reservations WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    return jsonify([dict(b) for b in bookings])

# ─── API: Contact Messages ────────────────────────────────────────────────────
@app.route('/api/contact', methods=['POST'])
def contact_submit():
    data = request.get_json() or {}
    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip()
    subject = str(data.get('subject', 'General Inquiry')).strip()
    message = str(data.get('message', '')).strip()

    if not name or not email or not message:
        return jsonify({'error': 'All fields are required'}), 400

    user_id = session.get('user_id')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as db:
        db.execute(
            'INSERT INTO contact_messages (user_id, name, email, subject, message, status, created_at) VALUES (?,?,?,?,?,?,?)',
            (user_id, name, email, subject, message, 'unread', created_at)
        )
        db.commit()
    return jsonify({'success': True, 'message': 'Message sent successfully!'})

# ─── API: Profile ─────────────────────────────────────────────────────────────
@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json() or {}
    full_name = str(data.get('full_name', '')).strip()
    phone = str(data.get('phone', '')).strip()
    address = str(data.get('address', '')).strip()
    if not full_name:
        return jsonify({'error': 'Name is required'}), 400
    with get_db() as db:
        db.execute('UPDATE users SET full_name=?, phone=?, address=? WHERE id=?',
                   (full_name, phone, address, session['user_id']))
        db.commit()
    session['user_name'] = full_name
    return jsonify({'success': True})

@app.route('/api/profile/password', methods=['PUT'])
@login_required
def update_password():
    data = request.get_json() or {}
    old_pw = str(data.get('old_password', ''))
    new_pw = str(data.get('new_password', ''))
    confirm_pw = str(data.get('confirm_password', ''))
    if len(new_pw) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    if new_pw != confirm_pw:
        return jsonify({'error': 'New passwords do not match'}), 400
    u = current_user()
    if not check_password_hash(u['password_hash'], old_pw):
        return jsonify({'error': 'Current password is incorrect'}), 400
    with get_db() as db:
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (generate_password_hash(new_pw), u['id']))
        db.commit()
    return jsonify({'success': True, 'message': 'Password updated successfully!'})

# ═══════════════════════════════════════════════════════════════════════════════
# ─── ADMIN APIs ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    with get_db() as db:
        revenue = db.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'cancelled'").fetchone()[0]
        total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending_orders = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]
        delivered_orders = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'delivered'").fetchone()[0]
        total_items = db.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
        total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_reservations = db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
        unread_messages = db.execute("SELECT COUNT(*) FROM contact_messages WHERE status = 'unread'").fetchone()[0]

    return jsonify({
        'revenue': round(revenue, 2),
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_items': total_items,
        'total_users': total_users,
        'total_reservations': total_reservations,
        'unread_messages': unread_messages
    })

@app.route('/api/admin/orders')
@admin_required
def admin_orders():
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    query = 'SELECT * FROM orders WHERE 1=1'
    params = []
    if status != 'all':
        query += ' AND status=?'
        params.append(status)
    if search:
        query += ' AND (id LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?)'
        wild = f'%{search}%'
        params.extend([wild, wild, wild])
    query += ' ORDER BY created_at DESC'

    with get_db() as db:
        orders = db.execute(query, params).fetchall()
        result = []
        for o in orders:
            order_dict = dict(o)
            items = db.execute('SELECT * FROM order_items WHERE order_id=?', (o['id'],)).fetchall()
            order_dict['items'] = [dict(i) for i in items]
            result.append(order_dict)
    return jsonify(result)

@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    valid_statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    with get_db() as db:
        db.execute('UPDATE orders SET status=? WHERE id=?', (new_status, order_id))
        db.commit()
    return jsonify({'success': True, 'status': new_status})

@app.route('/api/admin/menu', methods=['GET', 'POST'])
@admin_required
def admin_menu():
    with get_db() as db:
        if request.method == 'POST':
            data = request.get_json() or {}
            name = str(data.get('name', '')).strip()
            price = float(data.get('price', 0.0))
            category = str(data.get('category', 'pizza')).strip()
            image = str(data.get('image', '')).strip() or 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=700&q=80'
            description = str(data.get('description', '')).strip()
            is_veg = 1 if data.get('is_veg') else 0
            is_spicy = 1 if data.get('is_spicy') else 0
            is_featured = 1 if data.get('is_featured') else 0
            prep_time = str(data.get('prep_time', '15-20 mins')).strip()
            rating = float(data.get('rating', 4.8))

            if not name or price <= 0:
                return jsonify({'error': 'Valid name and price required'}), 400

            cursor = db.execute(
                '''INSERT INTO menu_items (name, price, category, image, description, available, is_veg, is_spicy, is_featured, prep_time, rating)
                   VALUES (?,?,?,?,?,1,?,?,?,?,?)''',
                (name, price, category, image, description, is_veg, is_spicy, is_featured, prep_time, rating)
            )
            db.commit()
            return jsonify({'success': True, 'id': cursor.lastrowid})

        items = db.execute('SELECT * FROM menu_items ORDER BY category, id DESC').fetchall()
        return jsonify([dict(i) for i in items])

@app.route('/api/admin/menu/<int:item_id>', methods=['PUT', 'DELETE'])
@admin_required
def admin_menu_item(item_id):
    with get_db() as db:
        if request.method == 'DELETE':
            db.execute('DELETE FROM menu_items WHERE id=?', (item_id,))
            db.commit()
            return jsonify({'success': True})

        data = request.get_json() or {}
        name = str(data.get('name', '')).strip()
        price = float(data.get('price', 0.0))
        category = str(data.get('category', '')).strip()
        image = str(data.get('image', '')).strip()
        description = str(data.get('description', '')).strip()
        is_veg = 1 if data.get('is_veg') else 0
        is_spicy = 1 if data.get('is_spicy') else 0
        is_featured = 1 if data.get('is_featured') else 0
        prep_time = str(data.get('prep_time', '20 mins')).strip()
        rating = float(data.get('rating', 4.8))

        db.execute(
            '''UPDATE menu_items SET name=?, price=?, category=?, image=?, description=?, is_veg=?, is_spicy=?, is_featured=?, prep_time=?, rating=?
               WHERE id=?''',
            (name, price, category, image, description, is_veg, is_spicy, is_featured, prep_time, rating, item_id)
        )
        db.commit()
        return jsonify({'success': True})

@app.route('/api/admin/menu/<int:item_id>/toggle', methods=['PUT'])
@admin_required
def admin_toggle_menu_item(item_id):
    with get_db() as db:
        item = db.execute('SELECT available FROM menu_items WHERE id=?', (item_id,)).fetchone()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        new_avail = 0 if item['available'] == 1 else 1
        db.execute('UPDATE menu_items SET available=? WHERE id=?', (new_avail, item_id))
        db.commit()
    return jsonify({'success': True, 'available': new_avail})

@app.route('/api/admin/reservations')
@admin_required
def admin_reservations():
    with get_db() as db:
        reservations = db.execute('SELECT * FROM reservations ORDER BY reservation_date DESC, reservation_time DESC').fetchall()
    return jsonify([dict(r) for r in reservations])

@app.route('/api/admin/reservations/<int:res_id>/status', methods=['PUT'])
@admin_required
def admin_update_reservation_status(res_id):
    data = request.get_json() or {}
    new_status = data.get('status', 'confirmed')
    with get_db() as db:
        db.execute('UPDATE reservations SET status=? WHERE id=?', (new_status, res_id))
        db.commit()
    return jsonify({'success': True, 'status': new_status})

@app.route('/api/admin/messages')
@admin_required
def admin_messages():
    with get_db() as db:
        messages = db.execute('SELECT * FROM contact_messages ORDER BY created_at DESC').fetchall()
    return jsonify([dict(m) for m in messages])

@app.route('/api/admin/messages/<int:msg_id>/status', methods=['PUT'])
@admin_required
def admin_update_message_status(msg_id):
    data = request.get_json() or {}
    status = data.get('status', 'resolved')
    with get_db() as db:
        db.execute('UPDATE contact_messages SET status=? WHERE id=?', (status, msg_id))
        db.commit()
    return jsonify({'success': True, 'status': status})

@app.route('/api/admin/messages/<int:msg_id>', methods=['DELETE'])
@admin_required
def admin_delete_message(msg_id):
    with get_db() as db:
        db.execute('DELETE FROM contact_messages WHERE id=?', (msg_id,))
        db.commit()
    return jsonify({'success': True})

@app.route('/api/admin/users')
@admin_required
def admin_users():
    with get_db() as db:
        users = db.execute('''
            SELECT u.id, u.full_name, u.email, u.phone, u.role, u.created_at,
                   COUNT(o.id) as order_count, COALESCE(SUM(o.total), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id AND o.status != 'cancelled'
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''').fetchall()
    return jsonify([dict(u) for u in users])

def is_streamlit_running():
    try:
        import streamlit as st
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx() is not None:
                return True
        except Exception:
            pass
        if any('streamlit' in str(arg).lower() for arg in sys.argv):
            return True
        if any(k.startswith('STREAMLIT') for k in os.environ.keys()):
            return True
        return False
    except ImportError:
        return False

# Auto-initialize database tables and seed data on load
init_db()

if is_streamlit_running():
    import st_ui
    st_ui.render_streamlit_interface(DB_PATH)
elif __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
