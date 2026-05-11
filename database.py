import sqlite3
from datetime import datetime

DB_FILE = "inventory.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        cost REAL NOT NULL,
        retail REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        expiry_date TEXT,
        arrival_date TEXT DEFAULT CURRENT_DATE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        qty_sold INTEGER,
        total_retail REAL,
        total_profit REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')

    c.execute("INSERT OR IGNORE INTO users VALUES ('admin','1234')")
    c.execute("DELETE FROM users WHERE rowid NOT IN (SELECT rowid FROM users ORDER BY rowid DESC LIMIT 1)")

    conn.commit()
    conn.close()

# ---------- USERS ----------
def verify_user(username, password):
    username = username.strip() if username else ''
    password = password or ''
    if not username or not password:
        return False

    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()
    return row is not None

def update_user(current_username, current_password, new_username, new_password):
    current_username = current_username.strip() if current_username else ''
    current_password = current_password or ''
    new_username = new_username.strip() if new_username else ''
    new_password = new_password or ''

    if not all([current_username, current_password, new_username, new_password]):
        return False, "All fields are required"

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT rowid FROM users WHERE username=? AND password=?",
            (current_username, current_password)
        )
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return False, "Invalid current credentials"

        current_rowid = row[0]

        # Remove any stale or duplicate rows for the new username before update.
        cursor.execute(
            "DELETE FROM users WHERE username=? AND rowid!=?",
            (new_username, current_rowid)
        )

        cursor.execute(
            "UPDATE users SET username=?, password=? WHERE rowid=?",
            (new_username, new_password, current_rowid)
        )

        # Ensure only one user row remains in the database.
        cursor.execute(
            "DELETE FROM users WHERE rowid!=?",
            (current_rowid,)
        )

        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return False, "Username already exists"
    finally:
        if conn:
            conn.close()

    return True, "Account updated successfully"

def reset_system_data():
    conn = get_conn()
    conn.execute("DELETE FROM products")
    conn.execute("DELETE FROM sales")
    conn.commit()
    conn.close()
    return True, "System data reset successfully"

# ---------- SALES ----------
def get_sales_report(date_from=None, date_to=None):
    conn = get_conn()
    query = "SELECT product_name, qty_sold, total_retail, total_profit, date FROM sales"
    params = []
    if date_from or date_to:
        query += " WHERE"
        if date_from:
            query += " date >= ?"
            params.append(date_from)
        if date_to:
            if date_from:
                query += " AND"
            query += " date <= ?"
            params.append(date_to + " 23:59:59")
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_sales_summary(date_from=None, date_to=None):
    conn = get_conn()
    query = "SELECT COUNT(*), SUM(total_retail), SUM(total_profit) FROM sales"
    params = []
    if date_from or date_to:
        query += " WHERE"
        if date_from:
            query += " date >= ?"
            params.append(date_from)
        if date_to:
            if date_from:
                query += " AND"
            query += " date <= ?"
            params.append(date_to + " 23:59:59")
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row

# ---------- PRODUCT MANAGEMENT ----------
def get_products():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, category, cost, retail, stock, expiry_date, arrival_date FROM products"
    ).fetchall()
    conn.close()
    return rows

def add_product(name, category, cost, retail, stock, expiry, arrival):
    conn = get_conn()
    if not arrival:
        arrival = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO products (name, category, cost, retail, stock, expiry_date, arrival_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, category, cost, retail, stock, expiry, arrival)
    )
    conn.commit()
    conn.close()

def edit_product(pid, name, category, cost, retail, stock, expiry):
    conn = get_conn()
    conn.execute(
        "UPDATE products SET name=?, category=?, cost=?, retail=?, stock=?, expiry_date=? WHERE id=?",
        (name, category, cost, retail, stock, expiry, pid)
    )
    conn.commit()
    conn.close()

def delete_product(pid):
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()

def get_product_by_id(pid):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, name, category, cost, retail, stock, expiry_date, arrival_date FROM products WHERE id=?",
        (pid,)
    ).fetchone()
    conn.close()
    return row

def get_product_cost(pid):
    conn = get_conn()
    row = conn.execute("SELECT cost FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    return row[0] if row else 0

def record_sale(pid, pname, qty, retail):
    conn = get_conn()
    cost = get_product_cost(pid)
    total_retail = retail * qty
    total_profit = (retail - cost) * qty
    conn.execute(
        "UPDATE products SET stock = stock - ? WHERE id=?",
        (qty, pid)
    )
    conn.execute(
        "INSERT INTO sales (product_name, qty_sold, total_retail, total_profit) VALUES (?, ?, ?, ?)",
        (pname, qty, total_retail, total_profit)
    )
    conn.commit()
    conn.close()
    return total_retail, total_profit