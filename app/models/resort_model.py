import sqlite3, hashlib, os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'resort.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def _col_names(cur, table):
    return [row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()]

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = get_db()
    cur = c.cursor()

    # ── CREATE TABLES ──────────────────────────────────────────
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL DEFAULT 'guest',
        created_at TEXT DEFAULT (datetime('now')))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS cottages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        inclusions TEXT,
        image_path TEXT,
        max_guests INTEGER DEFAULT 2,
        policy TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS reservations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cottage_id INTEGER NOT NULL REFERENCES cottages(id) ON DELETE CASCADE,
        guest_username TEXT NOT NULL,
        guest_email TEXT,
        date TEXT NOT NULL,
        shift TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        reference_no TEXT,
        total_price REAL NOT NULL,
        num_guests INTEGER DEFAULT 1,
        status TEXT DEFAULT 'confirmed',
        is_walkin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER UNIQUE NOT NULL,
        cottage_id INTEGER NOT NULL,
        guest_username TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')))""")

    # ── SAFE MIGRATIONS ────────────────────────────────────────
    user_cols = _col_names(cur, 'users')
    if 'email'      not in user_cols: cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if 'role'       not in user_cols: cur.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'guest'")
    if 'created_at' not in user_cols: cur.execute("ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")

    res_cols = _col_names(cur, 'reservations')
    if 'guest_email' not in res_cols: cur.execute("ALTER TABLE reservations ADD COLUMN guest_email TEXT")
    if 'is_walkin'   not in res_cols: cur.execute("ALTER TABLE reservations ADD COLUMN is_walkin INTEGER DEFAULT 0")
    if 'num_guests'  not in res_cols: cur.execute("ALTER TABLE reservations ADD COLUMN num_guests INTEGER DEFAULT 1")

    cot_cols = _col_names(cur, 'cottages')
    if 'is_active'   not in cot_cols: cur.execute("ALTER TABLE cottages ADD COLUMN is_active INTEGER DEFAULT 1")
    if 'max_guests'  not in cot_cols: cur.execute("ALTER TABLE cottages ADD COLUMN max_guests INTEGER DEFAULT 2")
    if 'policy'      not in cot_cols: cur.execute("ALTER TABLE cottages ADD COLUMN policy TEXT DEFAULT ''")

    # ── SEED ADMIN ─────────────────────────────────────────────
    cur.execute("SELECT id FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                    ('admin', hash_password('admin123'), 'admin'))

    # ── SEED COTTAGES ──────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM cottages")
    if cur.fetchone()[0] == 0:
        cottages = [
            ('Bahay Kubo A',      1500.0, 'Free Breakfast, 1hr Karaoke',   'kubo_a.jpg',       8,  'Good for small groups. No pets allowed. No outside food.'),
            ('Bahay Kubo B',      1500.0, 'Near Pool, Good for 10pax',     'kubo_b.jpg',       10, 'Near the pool area. Noise curfew at 10PM. No smoking inside.'),
            ('Modern Villa',      3500.0, 'Aircon, WiFi, Fridge',          'villa_sunset.jpg', 6,  'Full kitchen access. Keep unit clean. Towels provided.'),
            ('Poolside Umbrella',  500.0, 'Table & Chairs only',           'umbrella.jpg',     6,  'Outdoor area. No reservation of tables. First-come basis after booking.'),
            ('Couple Deluxe',     2500.0, 'Queen Bed, Aircon, TV',         'couple_room.jpg',  2,  'For couples only. No extra guests inside the room.'),
            ('Barkada Dorm',      4500.0, '6 Bunk Beds, Aircon, Locker',   'dorm.jpg',         12, 'Locker deposit required. Keep common areas tidy. Lights out by 12MN.'),
            ('Grand Suite',       8000.0, 'Glass House, Bathtub, Netflix', 'suite.jpg',        4,  'Premium unit. Damage deposit required. No parties or events.'),
        ]
        cur.executemany(
            "INSERT INTO cottages(name,price,inclusions,image_path,max_guests,policy) VALUES(?,?,?,?,?,?)",
            cottages)

    c.commit()
    c.close()


# ─── USER MODEL ───────────────────────────────────────────────
class UserModel:
    @staticmethod
    def find_by_username(username):
        c = get_db()
        row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        c.close(); return row

    @staticmethod
    def create(username, password, email=None):
        c = get_db()
        try:
            c.execute("INSERT INTO users(username,password,email,role) VALUES(?,?,?,?)",
                      (username, hash_password(password), email or None, 'guest'))
            c.commit(); return True
        except sqlite3.IntegrityError: return False
        finally: c.close()

    @staticmethod
    def verify(username, password):
        row = UserModel.find_by_username(username)
        return row if row and row['password'] == hash_password(password) else None

    @staticmethod
    def update_password(username, new_password):
        c = get_db()
        c.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new_password), username))
        c.commit(); c.close()

    @staticmethod
    def update_email(username, email):
        c = get_db()
        c.execute("UPDATE users SET email=? WHERE username=?", (email, username))
        c.commit(); c.close()

    @staticmethod
    def get_all():
        c = get_db()
        rows = c.execute("""
            SELECT id, username, COALESCE(email,'') as email,
                   role, COALESCE(created_at,'') as created_at
            FROM users WHERE role='guest' ORDER BY created_at DESC
        """).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def delete(username):
        c = get_db()
        c.execute("DELETE FROM users WHERE username=? AND role='guest'", (username,))
        c.commit(); c.close()


# ─── COTTAGE MODEL ────────────────────────────────────────────
class CottageModel:
    @staticmethod
    def get_all():
        c = get_db()
        rows = c.execute("SELECT * FROM cottages WHERE is_active=1 ORDER BY price ASC").fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(cid):
        c = get_db()
        row = c.execute("SELECT * FROM cottages WHERE id=?", (cid,)).fetchone()
        c.close(); return dict(row) if row else None

    @staticmethod
    def create(name, price, inclusions, image_path, max_guests=2, policy=''):
        c = get_db()
        try:
            c.execute("INSERT INTO cottages(name,price,inclusions,image_path,max_guests,policy) VALUES(?,?,?,?,?,?)",
                      (name, price, inclusions, image_path, max_guests, policy))
            c.commit(); return True
        except sqlite3.IntegrityError: return False
        finally: c.close()

    @staticmethod
    def update(cid, name, price, inclusions, image_path=None, max_guests=None, policy=None):
        c = get_db()
        try:
            if image_path:
                c.execute("UPDATE cottages SET name=?,price=?,inclusions=?,image_path=?,max_guests=?,policy=? WHERE id=?",
                          (name, price, inclusions, image_path, max_guests, policy, cid))
            else:
                c.execute("UPDATE cottages SET name=?,price=?,inclusions=?,max_guests=?,policy=? WHERE id=?",
                          (name, price, inclusions, max_guests, policy, cid))
            c.commit(); return True
        except sqlite3.IntegrityError: return False
        finally: c.close()

    @staticmethod
    def delete(cid):
        c = get_db()
        c.execute("DELETE FROM cottages WHERE id=?", (cid,))
        c.commit(); c.close()

    @staticmethod
    def get_all_for_admin():
        c = get_db()
        rows = c.execute("""
            SELECT c.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.id) as review_count
            FROM cottages c
            LEFT JOIN reviews r ON c.id = r.cottage_id
            WHERE c.is_active = 1
            GROUP BY c.id ORDER BY c.id DESC
        """).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_booked_dates(cid):
        c = get_db()
        rows = c.execute("""
            SELECT date, shift FROM reservations
            WHERE cottage_id=? AND status='confirmed' AND date >= date('now')
        """, (cid,)).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_reviews(cid):
        c = get_db()
        rows = c.execute("SELECT * FROM reviews WHERE cottage_id=? ORDER BY created_at DESC", (cid,)).fetchall()
        c.close(); return [dict(r) for r in rows]


# ─── RESERVATION MODEL ────────────────────────────────────────
class ReservationModel:
    @staticmethod
    def is_booked(cid, dt, shift, exclude_id=None):
        c = get_db()
        if exclude_id:
            row = c.execute("""SELECT id FROM reservations
                WHERE cottage_id=? AND date=? AND shift=? AND status='confirmed' AND id!=?""",
                (cid, dt, shift, exclude_id)).fetchone()
        else:
            row = c.execute("""SELECT id FROM reservations
                WHERE cottage_id=? AND date=? AND shift=? AND status='confirmed'""",
                (cid, dt, shift)).fetchone()
        c.close(); return row is not None

    @staticmethod
    def create(cid, guest, guest_email, dt, shift, payment, reference, total, is_walkin=0, num_guests=1):
        c = get_db()
        c.execute("""INSERT INTO reservations
            (cottage_id,guest_username,guest_email,date,shift,payment_method,reference_no,total_price,is_walkin,num_guests)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (cid, guest, guest_email, dt, shift, payment, reference, total, is_walkin, num_guests))
        c.commit()
        rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.close()
        NotificationModel.create('booking', f'New booking by {guest} for {dt} ({shift})')
        return rid

    @staticmethod
    def reschedule(rid, username, new_date, new_shift, new_total):
        c = get_db()
        c.execute("""UPDATE reservations SET date=?,shift=?,total_price=?
            WHERE id=? AND guest_username=? AND status='confirmed'""",
            (new_date, new_shift, new_total, rid, username))
        c.commit(); c.close()

    @staticmethod
    def cancel(rid, username=None):
        c = get_db()
        if username:
            c.execute("UPDATE reservations SET status='cancelled' WHERE id=? AND guest_username=?", (rid, username))
        else:
            c.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (rid,))
        c.commit(); c.close()
        NotificationModel.create('cancellation', f'Reservation #{rid} was cancelled.')

    @staticmethod
    def get_all():
        c = get_db()
        rows = c.execute("""
            SELECT r.*, c.name as cottage_name
            FROM reservations r JOIN cottages c ON r.cottage_id=c.id
            ORDER BY r.created_at DESC
        """).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_by_user(username):
        c = get_db()
        rows = c.execute("""
            SELECT r.*, c.name as cottage_name, c.image_path, c.id as cottage_id
            FROM reservations r JOIN cottages c ON r.cottage_id=c.id
            WHERE r.guest_username=? ORDER BY r.created_at DESC
        """, (username,)).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(rid):
        c = get_db()
        row = c.execute("""
            SELECT r.*, c.name as cottage_name, c.price as cottage_price, c.max_guests
            FROM reservations r JOIN cottages c ON r.cottage_id=c.id
            WHERE r.id=?
        """, (rid,)).fetchone()
        c.close(); return dict(row) if row else None

    @staticmethod
    def get_stats():
        c = get_db()
        row = c.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(CASE WHEN status='confirmed' THEN total_price END),0) as revenue,
                   COUNT(CASE WHEN date=date('now') AND status='confirmed' THEN 1 END) as today
            FROM reservations
        """).fetchone()
        c.close(); return dict(row)

    @staticmethod
    def get_monthly_revenue():
        c = get_db()
        rows = c.execute("""
            SELECT strftime('%Y-%m',date) as month,
                   COALESCE(SUM(total_price),0) as revenue,
                   COUNT(*) as bookings
            FROM reservations WHERE status='confirmed'
            GROUP BY month ORDER BY month DESC LIMIT 12
        """).fetchall()
        c.close(); return [dict(r) for r in reversed(rows)]

    @staticmethod
    def get_all_csv():
        c = get_db()
        rows = c.execute("""
            SELECT r.id, c.name as cottage_name, r.guest_username, r.guest_email,
                   r.date, r.shift, r.payment_method, r.reference_no, r.total_price,
                   r.num_guests, r.status, r.is_walkin, r.created_at
            FROM reservations r JOIN cottages c ON r.cottage_id=c.id
            ORDER BY r.created_at DESC
        """).fetchall()
        c.close(); return [dict(r) for r in rows]


# ─── REVIEW MODEL ─────────────────────────────────────────────
class ReviewModel:
    @staticmethod
    def exists(reservation_id):
        c = get_db()
        row = c.execute("SELECT id FROM reviews WHERE reservation_id=?", (reservation_id,)).fetchone()
        c.close(); return row is not None

    @staticmethod
    def create(reservation_id, cottage_id, guest_username, rating, comment):
        c = get_db()
        try:
            c.execute("INSERT INTO reviews(reservation_id,cottage_id,guest_username,rating,comment) VALUES(?,?,?,?,?)",
                      (reservation_id, cottage_id, guest_username, rating, comment))
            c.commit(); return True
        except sqlite3.IntegrityError: return False
        finally: c.close()

    @staticmethod
    def get_all():
        c = get_db()
        rows = c.execute("""
            SELECT rv.*, c.name as cottage_name
            FROM reviews rv JOIN cottages c ON rv.cottage_id=c.id
            ORDER BY rv.created_at DESC
        """).fetchall()
        c.close(); return [dict(r) for r in rows]


# ─── NOTIFICATION MODEL ───────────────────────────────────────
class NotificationModel:
    @staticmethod
    def create(ntype, message):
        c = get_db()
        c.execute("INSERT INTO notifications(type,message) VALUES(?,?)", (ntype, message))
        c.commit(); c.close()

    @staticmethod
    def get_recent(limit=20):
        c = get_db()
        rows = c.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        c.close(); return [dict(r) for r in rows]

    @staticmethod
    def get_unread_count():
        c = get_db()
        row = c.execute("SELECT COUNT(*) FROM notifications WHERE is_read=0").fetchone()
        c.close(); return row[0]

    @staticmethod
    def mark_all_read():
        c = get_db()
        c.execute("UPDATE notifications SET is_read=1")
        c.commit(); c.close()
