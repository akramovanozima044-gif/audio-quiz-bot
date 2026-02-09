import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def init_db():
    """Database yaratish va jadvallarni ishga tushirish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Users jadvali (faqat admin va ruxsat berilgan userlar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_admin BOOLEAN DEFAULT 0,
            is_allowed BOOLEAN DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin sozlamalari
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allow_group_add BOOLEAN DEFAULT 0,
            require_permission BOOLEAN DEFAULT 1
        )
    ''')
    
    # Avvalgi ma'lumotlarni tozalash
    cursor.execute("DELETE FROM admin_settings")
    
    # Default sozlamalarni qo'shish (A-qadam shartlari)
    cursor.execute('''
        INSERT INTO admin_settings (allow_group_add, require_permission) 
        VALUES (0, 1)
    ''')
    
    # Access requests - foydalanuvchilarning ruxsat so'rovlari
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def add_user_if_not_exists(user_id, username, first_name, is_admin=False):
    """Foydalanuvchi mavjud bo'lmasa qo'shish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )
    
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, is_admin, is_allowed)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, 1 if is_admin else 0, 1 if is_admin else 0))
    
    conn.commit()
    conn.close()

def is_user_allowed(user_id):
    """Foydalanuvchiga ruxsat berilganligini tekshirish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT is_allowed FROM users WHERE user_id = ?",
        (user_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else False

def is_user_admin(user_id):
    """Foydalanuvchi admin ekanligini tekshirish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT is_admin FROM users WHERE user_id = ?",
        (user_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else False

def get_admin_settings():
    """Admin sozlamalarini olish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admin_settings LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'allow_group_add': bool(result[1]),
            'require_permission': bool(result[2])
        }
    return {'allow_group_add': False, 'require_permission': True}

def add_access_request(user_id, username, first_name):
    """Ruxsat so'rovini qo'shish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Oldingi pending so'rovlarni bekor qilish
    cursor.execute(
        "UPDATE access_requests SET status = 'cancelled' WHERE user_id = ? AND status = 'pending'",
        (user_id,)
    )
    
    cursor.execute('''
        INSERT INTO access_requests (user_id, username, first_name, status)
        VALUES (?, ?, ?, 'pending')
    ''', (user_id, username, first_name))
    
    conn.commit()
    conn.close()

def get_pending_requests():
    """Kutilayotgan ruxsat so'rovlarini olish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, username, first_name, request_date 
        FROM access_requests 
        WHERE status = 'pending'
        ORDER BY request_date
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'id': r[0],
        'user_id': r[1],
        'username': r[2],
        'first_name': r[3],
        'request_date': r[4]
    } for r in results]

def update_access_request(request_id, status, admin_id):
    """Ruxsat so'rovini yangilash"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Request statusini yangilash
    cursor.execute(
        "UPDATE access_requests SET status = ? WHERE id = ?",
        (status, request_id)
    )
    
    # Agar ruxsat berilsa, userni allowed qilish
    if status == 'approved':
        cursor.execute(
            "SELECT user_id FROM access_requests WHERE id = ?",
            (request_id,)
        )
        user_request = cursor.fetchone()
        
        if user_request:
            user_id = user_request[0]
            cursor.execute(
                "UPDATE users SET is_allowed = 1 WHERE user_id = ?",
                (user_id,)
            )
    
    conn.commit()
    conn.close()

def get_all_users():
    """Barcha foydalanuvchilarni olish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, first_name, is_allowed, join_date 
        FROM users 
        ORDER BY join_date DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': r[0],
        'username': r[1],
        'first_name': r[2],
        'is_allowed': bool(r[3]),
        'join_date': r[4]
    } for r in results]

def remove_user(user_id):
    """Foydalanuvchini o'chirish"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM access_requests WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()