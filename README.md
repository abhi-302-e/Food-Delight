# 🍽️ Foodie Delight – Advanced Gourmet Restaurant Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

**Foodie Delight** is an enterprise-grade, full-stack gourmet restaurant and online food ordering web platform built with **Python (Flask)**, **SQLite3**, and modern vanilla JavaScript and CSS. It delivers fine-dining restaurant aesthetics with lightning-fast delivery workflows, comprehensive customer management, and an executive administration console.

---

## ✨ Key Upgrades & Features

### 🛡️ 1. Executive Admin Management Console (`/admin`)
- **Real-Time KPI Dashboard**: Live stats tracking total revenue ($), total orders, pending orders, delivered orders, active dishes, table bookings, registered customers, and unread inquiries.
- **Order Lifecycle Management**: View full customer details, delivery address, phone, item breakdowns, and update order statuses in real time:
  `Pending` ➔ `Confirmed` ➔ `Preparing` ➔ `Out for Delivery` ➔ `Delivered` ➔ `Cancelled`.
- **Menu CRUD Manager**:
  - Full catalog of 33+ dishes across 6 categories.
  - Add new dishes with image preview, prep time, price, tags (🌱 Veg, 🌶️ Spicy, ⭐ Chef's Special).
  - Edit existing menu items inline or through the modal.
  - Instant one-click availability toggle (In Stock / Out of Stock).
  - Delete dishes with confirmation safety.
- **Table Reservations Manager**: Manage dine-in seating requests, party size, table preferences, and update booking statuses.
- **Customer Feedback & Inquiries**: View messages submitted via the Contact form, mark as resolved, or remove.
- **User Directory**: View registered customer profiles, total orders count, and lifetime spend.

---

### 🍕 2. Expanded 33+ Dish Gourmet Menu (6 Categories)
- **Wood-Fired Pizzas (6)**: Margherita Di Bufala, Double Pepperoni Rustica, Truffle & Wild Mushroom, Smokey BBQ Chicken, Fiery Diavola, Paneer Tikka Supreme.
- **Artisan Burgers (6)**: Classic Angus Cheeseburger, Crispy Buttermilk Chicken, Double Truffle Wagyu Smash, Fiery Bacon Jalapeño, Gourmet Portobello, Garden Harvest Black Bean.
- **Gourmet Sandwiches & Paninis (5)**: Grand Triple-Decker Club, Avocado & Burrata Sourdough, Grilled Chicken Pesto Panini, Philly Cheesesteak Melt, Smoked Salmon Bagel Deluxe.
- **Pastas & Mains (5)**: Handcrafted Fettuccine Alfredo, Slow-Cooked Bolognese Tagliatelle, Penne Alla Vodka with Pancetta, Wild Mushroom Truffle Risotto, Pan-Seared Lemon Herb Salmon.
- **Starters & Tapas (5)**: Truffle Parmesan Hand-Cut Fries, Crispy Buffalo Wings, Golden Calamari Fritti, Cheesy Garlic Herb Pull-Apart Bread, Mediterranean Mezze Platter.
- **Desserts & Artisanal Beverages (6)**: Belgian Molten Chocolate Lava Cake, New York Berry Cheesecake, Artisanal Coffee Tiramisu, Tropical Mango Passionfruit Cooler, Iced Caramel Macchiato, Wild Berry Mint Mojito.

---

### 📅 3. Dine-In Table Reservation System (`/reservations`)
- Seamless booking form with party size selection (1 to 10+ guests).
- Date picker with past date prevention.
- Lunch & Dinner time slots.
- Seating preferences: *Indoor Main Dining, Romantic Window Booth, Outdoor Garden Patio, Private Dining Salon, Chef's Open Counter*.
- Special occasions: *Birthday Celebration, Anniversary, Romantic Date Night, Business Dinner*.
- Instant confirmation and tracking for logged-in users.

---

### 📦 4. Visual Order Tracking & Stepper (`/orders`)
- Live progress timeline:
  `Order Placed` ➔ `Confirmed` ➔ `Preparing` ➔ `Out for Delivery` ➔ `Delivered`.
- Itemized receipts with quantities, subtotals, applied discount, delivery address, phone, and payment method.

---

### 🏷️ 5. Promo Codes & Shopping Cart Drawer
- Persistent `localStorage` cart with live badge counters.
- Built-in promo coupon engine:
  - `WELCOME20` — 20% discount on order total
  - `FOODIE10` — $10 discount
  - `TASTY15` — 15% discount
- Flexible payment methods: Cash on Delivery, Credit/Debit Card, UPI / Online QR.

---

### 🔍 6. Interactive Search, Filter & Sort
- Real-time debounced search bar on `/menu`.
- Category quick pills (*All, Pizzas, Burgers, Pastas & Mains, Sandwiches, Starters, Desserts*).
- Dietary tags filter (*All, 🌱 Vegetarian, 🌶️ Spicy, ⭐ Chef's Special*).
- Sorting options (*Recommended, Price Low-to-High, Price High-to-Low, Highest Rated*).

---

## 🔑 Demo Credentials

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Master Admin** | `admin@foodiedelight.com` | `admin123` | Full Admin Dashboard & Storefront |
| **Customer** | `as@gmail.com` | *(Registered password)* | Ordering, Cart, Tracking, Profile |

*(You can also register a new account on `/register` to test customer flows).*

---

## 📁 Project Structure

```
Food-Delight/
├── app.py                      # Core Flask Application & API Routes
├── requirements.txt            # Python Dependencies
├── foodie_delight.db           # SQLite Database (Auto-migrated & seeded)
├── README.md                   # Project Documentation
├── static/
│   ├── css/
│   │   ├── style.css           # Modern Restaurant Design System & Animations
│   │   ├── auth.css            # Authentication & Profile Styles
│   │   └── admin.css           # Executive Admin Dashboard Styles
│   ├── js/
│   │   ├── app.js              # Storefront Cart, Search, Modals & Checkout
│   │   └── admin.js            # Admin Dashboard Tabs, CRUD, Orders & Stats
│   └── img/
│       ├── logo.png            # Restaurant Branding Logo
│       ├── food-bg.jpg         # Hero & Fallback Imagery
│       ├── search-bg.jpg       # Search Background Asset
│       ├── category/           # Category Imagery (Burger, Pizza, Sandwich)
│       └── food/               # Food Thumbnails
└── templates/
    ├── base.html               # Master Layout (Header, Cart Drawer, Footer)
    ├── index.html              # Modern Restaurant Landing Page
    ├── menu.html               # Full Menu with Search, Filter & Sort
    ├── reservations.html       # Table Booking & Reservation Hub
    ├── orders.html             # Order History & Live Visual Stepper
    ├── profile.html            # User Account Management
    ├── contact.html            # Contact & Support Inquiries Form
    ├── about.html              # Our Story & Four Pillars Philosophy
    ├── login.html              # Sign In (with 1-click Demo Fill)
    ├── register.html           # User Registration Page
    └── admin.html              # Complete Admin Operations Portal
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/abhi-302-e/Food-Delight.git
cd Food-Delight
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

### 4. Open in your browser
- **Storefront**: [http://localhost:5000](http://localhost:5000)
- **Admin Portal**: [http://localhost:5000/admin](http://localhost:5000/admin) *(Sign in with admin credentials)*

---

## 📡 REST API Documentation

### Public & Customer Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/menu` | Query menu items (`?category=&diet=&sort=&search=`) |
| `GET` | `/api/menu/featured` | Fetch top signature chef specials |
| `POST` | `/api/coupon/validate` | Validate promo discount codes |
| `POST` | `/api/orders` | Place an order (requires auth) |
| `GET` | `/api/orders` | List logged-in user's past orders |
| `GET` | `/api/orders/<id>` | Get order items and delivery details |
| `POST` | `/api/reservations` | Book a dine-in table |
| `GET` | `/api/reservations/my` | View user's table reservations |
| `POST` | `/api/contact` | Submit contact inquiry |
| `PUT` | `/api/profile` | Update profile information |

### Admin Endpoints (Requires Admin Role)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/stats` | KPI statistics & revenue summary |
| `GET` | `/api/admin/orders` | View all customer orders with item details |
| `PUT` | `/api/admin/orders/<id>/status` | Update order preparation/delivery status |
| `GET` | `/api/admin/menu` | View all menu items |
| `POST` | `/api/admin/menu` | Add a new dish to the catalog |
| `PUT` | `/api/admin/menu/<id>` | Update dish details and price |
| `PUT` | `/api/admin/menu/<id>/toggle` | Toggle in-stock / out-of-stock |
| `DELETE` | `/api/admin/menu/<id>` | Permanently remove dish |
| `GET` | `/api/admin/reservations` | View guest table bookings |
| `PUT` | `/api/admin/reservations/<id>/status`| Update reservation status |
| `GET` | `/api/admin/messages` | View customer inquiries |
| `PUT` | `/api/admin/messages/<id>/status`| Mark inquiry resolved |
| `DELETE` | `/api/admin/messages/<id>` | Delete inquiry |
| `GET` | `/api/admin/users` | View registered customer directory |

---

## 🛠️ Built With
- **Backend**: Python 3, Flask, SQLite3, Werkzeug Security
- **Frontend**: HTML5, Semantic CSS3, Vanilla JavaScript (ES6+)
- **Design System**: Responsive Grid, Flexbox, Custom Color Variables, FontAwesome Icons, Google Fonts (`Plus Jakarta Sans` & `Playfair Display`)

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
