import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id TEXT UNIQUE,
    username TEXT,
    is_premium INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    premium_expiry TEXT
)
''')

# Create links table
cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    telegram_id TEXT,
    url TEXT,
    interval INTEGER,
    added_at TEXT,
    expires_at TEXT,
    active INTEGER DEFAULT 1
)
''')

conn.commit()

# USER METHODS
def add_user(telegram_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
    conn.commit()

def update_referral(telegram_id):
    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()

def get_user(telegram_id):
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone()

def set_premium(telegram_id, months):
    expiry = (datetime.now() + timedelta(days=30 * months)).isoformat()
    cursor.execute("UPDATE users SET is_premium = 1, premium_expiry = ? WHERE telegram_id = ?", (expiry, telegram_id))
    conn.commit()

# LINK METHODS
def add_link(telegram_id, url, interval, duration_days):
    now = datetime.now()
    expires = now + timedelta(days=duration_days)
    cursor.execute("INSERT INTO links (telegram_id, url, interval, added_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                   (telegram_id, url, interval, now.isoformat(), expires.isoformat()))
    conn.commit()

def get_links_by_user(telegram_id):
    cursor.execute("SELECT * FROM links WHERE telegram_id = ? AND active = 1", (telegram_id,))
    return cursor.fetchall()

def stop_link(link_id):
    cursor.execute("UPDATE links SET active = 0 WHERE id = ?", (link_id,))
    conn.commit()

def delete_expired_links():
    now = datetime.now().isoformat()
    cursor.execute("UPDATE links SET active = 0 WHERE expires_at < ?", (now,))
    conn.commit()

def get_all_active_links():
    cursor.execute("SELECT * FROM links WHERE active = 1")
    return cursor.fetchall()
