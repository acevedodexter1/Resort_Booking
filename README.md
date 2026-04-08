# 🌴 Paradise Resort — Flask Web App

A full-stack Resort Booking System built with **Python Flask** (MVC architecture),
**SQLite** database, and a **HTML/CSS/JS** frontend with a luxury tropical aesthetic.

---

## 📁 Project Structure (MVC)

```
resort_flask/
├── run.py                        ← Entry point
├── requirements.txt
├── instance/
│   └── resort.db                 ← SQLite database (auto-created)
└── app/
    ├── __init__.py               ← App factory
    ├── models/
    │   └── resort_model.py       ← M: Database logic (Users, Cottages, Reservations)
    ├── controllers/
    │   ├── auth_controller.py    ← C: Login, Register, Logout
    │   ├── guest_controller.py   ← C: Dashboard, Booking, My Bookings
    │   └── admin_controller.py   ← C: Admin CRUD operations
    ├── views/
    │   └── templates/            ← V: Jinja2 HTML templates
    │       ├── base.html
    │       ├── welcome.html
    │       ├── login.html
    │       ├── dashboard.html
    │       ├── booking.html
    │       ├── my_bookings.html
    │       └── admin.html
    └── static/
        ├── css/main.css
        ├── js/main.js
        └── images/
```

---

## ⚙️ Setup & Run (VS Code / Terminal)

### 1. Install Python
Download from https://python.org (Python 3.10+ recommended)

### 2. Open terminal in the `resort_flask` folder
```
cd resort_flask
```

### 3. Create a virtual environment
```bash
python -m venv venv
```

### 4. Activate the virtual environment
- **Windows:**  `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the app
```bash
python run.py
```

### 7. Open in browser
```
http://localhost:5000
```

---

## 🔐 Default Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | admin123  |
| Guest | (register your own account) | — |

---

## 🗄️ Database (SQLite — DB Browser compatible)

The database file is at: `instance/resort.db`

You can open it directly in **DB Browser for SQLite**:
- Download: https://sqlitebrowser.org
- Open File → `instance/resort.db`
- Tables: `users`, `cottages`, `reservations`

---

## ✨ Features

- **Welcome Page** — Animated hero, particle effects, showcase strip
- **Guest Login/Register** — 3D card flip animation, password visibility toggle
- **Guest Dashboard** — Cottage grid with search & price filters
- **Booking Page** — Date picker (no past dates), shift selector, payment method
- **My Bookings** — View and cancel reservations
- **Admin Dashboard** — Stats counters, tabbed interface:
  - 📦 Inventory: Add/delete accommodations with image upload
  - 👥 Guests: View and remove registered guests
  - 📈 Reports: Full transaction history with revenue summary

## 🔒 Security Features

- SHA-256 password hashing
- CSRF protection on all forms (Flask-WTF)
- Session-based authentication with 2-hour timeout
- Input validation (server + client side)
- SQL injection prevention (parameterized queries)
- File upload validation (images only, UUID filenames)
- Admin route protection middleware
- Past-date booking prevention
