"""
Database operations for the GT-Bot.
"""

import sqlite3
import time
from datetime import datetime

from .config import DATABASE_PATH, MY_TZ, sessions, SESSION_TIMEOUT


def now_myt():
    """Get current time in Malaysian timezone as ISO string for SQLite"""
    return datetime.now(MY_TZ).strftime('%Y-%m-%d %H:%M:%S')


def get_db():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)


def is_user_registered(telegram_id):
    """Check if user exists and is allowed"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_allowed FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]  # Returns is_allowed (True/False)
    return None  # Not registered


def register_user(telegram_id, username, first_name, last_name, invite_code):
    """Register user with invite code"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check invite code
    cursor.execute("SELECT id, is_used FROM invite_codes WHERE code = ?", (invite_code,))
    invite = cursor.fetchone()
    
    if not invite:
        conn.close()
        return False, "Invalid invite code."
    
    if invite[1]:  # is_used
        conn.close()
        return False, "This invite code has already been used."
    
    invite_id = invite[0]
    
    # Create user
    try:
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, invite_id, is_allowed, last_activity)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (telegram_id, username, first_name, last_name, invite_id, now_myt()))
        
        # Mark invite as used
        cursor.execute("""
            UPDATE invite_codes SET is_used = 1, telegram_id = ?, used_at = ?
            WHERE id = ?
        """, (telegram_id, now_myt(), invite_id))
        
        conn.commit()
        conn.close()
        return True, "Registration successful! You can now start chatting."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "You are already registered."


def update_session(telegram_id):
    """Update session timestamp"""
    sessions[telegram_id] = time.time()
    
    # Also update last_activity in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_activity = ? WHERE telegram_id = ?", (now_myt(), telegram_id))
    conn.commit()
    conn.close()


def is_session_valid(telegram_id):
    """Check if session is still valid"""
    if telegram_id not in sessions:
        return False
    if time.time() - sessions[telegram_id] > SESSION_TIMEOUT:
        del sessions[telegram_id]
        return False
    return True


def log_chat(telegram_id, message_type, content, file_name, bot_response):
    """Log chat to database"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user_id
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return
    
    cursor.execute("""
        INSERT INTO chat_logs (user_id, message_type, content, file_name, bot_response, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user[0], message_type, content, file_name, bot_response, now_myt()))
    
    conn.commit()
    conn.close()


def get_voice_enabled(telegram_id):
    """Get user's voice preference from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT voice_enabled FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return bool(result[0])
    return False


def set_voice_enabled(telegram_id, enabled):
    """Set user's voice preference in database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET voice_enabled = ? WHERE telegram_id = ?", (1 if enabled else 0, telegram_id))
    conn.commit()
    conn.close()


def init_persistent_memory_table():
    """Create the user_persistent_memory table if it doesn't exist."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_persistent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(telegram_id, category, key)
        )
    """)
    conn.commit()
    conn.close()
    print("[Database] Persistent memory table initialized")


# Initialize the persistent memory table on module load
init_persistent_memory_table()
