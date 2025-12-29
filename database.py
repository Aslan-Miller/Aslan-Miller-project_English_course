import sqlite3
import datetime

def get_db():
    conn = sqlite3.connect('english_bot.db')
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        end_date TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных готова")

def add_user(user_id, username, first_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name) 
    VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()

def has_active_subscription(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT end_date FROM subscriptions 
    WHERE user_id = ? 
    ORDER BY end_date DESC LIMIT 1
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        end_date = datetime.datetime.fromisoformat(result[0])
        return end_date > datetime.datetime.now()
    return False

def give_subscription(user_id, days=30):
    conn = get_db()
    cursor = conn.cursor()
    end_date = datetime.datetime.now() + datetime.timedelta(days=days)
    
    cursor.execute('''
    INSERT INTO subscriptions (user_id, end_date) 
    VALUES (?, ?)
    ''', (user_id, end_date.isoformat()))
    
    conn.commit()
    conn.close()
    return end_date

def create_payments_table():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending',
        message_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_payment(user_id, amount, message_text=""):
    create_payments_table()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO payments (user_id, amount, message_text)
    VALUES (?, ?, ?)
    ''', (user_id, amount, message_text))
    
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return payment_id

def get_pending_payments():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT p.id, p.user_id, u.username, u.first_name, p.amount, p.message_text, p.created_at
    FROM payments p
    LEFT JOIN users u ON p.user_id = u.user_id
    WHERE p.status = 'pending'
    ORDER BY p.created_at DESC
    ''')
    
    payments = cursor.fetchall()
    conn.close()
    return payments

def approve_payment(payment_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, amount FROM payments WHERE id = ?', (payment_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    user_id, amount = result
    
    days = 30 if amount >= 299 else 7
    give_subscription(user_id, days)
    
    cursor.execute('UPDATE payments SET status = "approved" WHERE id = ?', (payment_id,))
    
    conn.commit()
    conn.close()
    return True

def reject_payment(payment_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE payments SET status = "rejected" WHERE id = ?', (payment_id,))
    
    conn.commit()
    conn.close()
    return True

init_db()