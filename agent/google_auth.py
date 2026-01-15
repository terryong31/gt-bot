"""
Google OAuth Authentication Module
Handles per-user Google OAuth flow and token management.
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import sqlite3

# OAuth Scopes for Google Services
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/tasks',  
]

# Get configuration from environment
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Database path (same as main bot)
DATABASE_PATH = os.getenv('DATABASE_PATH', '/app/data/bot.db')


def get_db():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)


def init_google_tokens_table():
    """Initialize the google_tokens table if it doesn't exist"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS google_tokens (
            telegram_id INTEGER PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_expiry TEXT NOT NULL,
            scopes TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def get_oauth_flow() -> Flow:
    """Create OAuth flow with client credentials"""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    return flow


def get_auth_url(telegram_id: int) -> str:
    """
    Generate Google OAuth authorization URL.
    The telegram_id is encoded in the state parameter.
    """
    flow = get_oauth_flow()
    
    # Encode telegram_id in state for callback identification
    state = json.dumps({"telegram_id": telegram_id})
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    
    return auth_url


def exchange_code(code: str, state: str) -> Tuple[bool, str, Optional[int]]:
    """
    Exchange authorization code for tokens.
    Returns (success, message, telegram_id)
    """
    try:
        # Parse state to get telegram_id
        state_data = json.loads(state)
        telegram_id = state_data.get("telegram_id")
        
        if not telegram_id:
            return False, "Invalid state: missing telegram_id", None
        
        # Exchange code for tokens
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Store tokens in database
        conn = get_db()
        cursor = conn.cursor()
        
        # Upsert token
        cursor.execute('''
            INSERT OR REPLACE INTO google_tokens 
            (telegram_id, access_token, refresh_token, token_expiry, scopes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            telegram_id,
            credentials.token,
            credentials.refresh_token,
            credentials.expiry.isoformat() if credentials.expiry else None,
            json.dumps(list(credentials.scopes)) if credentials.scopes else json.dumps(SCOPES),
            datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return True, "Successfully linked Google account!", telegram_id
        
    except Exception as e:
        return False, f"Error exchanging code: {str(e)}", None


def get_credentials(telegram_id: int) -> Optional[Credentials]:
    """
    Get valid Google credentials for a user.
    Returns None if user hasn't linked Google or tokens are invalid.
    Automatically refreshes expired tokens.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT access_token, refresh_token, token_expiry, scopes FROM google_tokens WHERE telegram_id = ?',
        (telegram_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    access_token, refresh_token, token_expiry, scopes_json = row
    
    # Parse expiry
    expiry = None
    if token_expiry:
        try:
            expiry = datetime.fromisoformat(token_expiry.replace('Z', '+00:00'))
        except:
            pass
    
    # Parse scopes
    try:
        scopes = json.loads(scopes_json)
    except:
        scopes = SCOPES
    
    # Create credentials object
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=scopes,
        expiry=expiry
    )
    
    # Check if expired and refresh
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            
            # Update stored tokens
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE google_tokens 
                SET access_token = ?, token_expiry = ?
                WHERE telegram_id = ?
            ''', (
                credentials.token,
                credentials.expiry.isoformat() if credentials.expiry else None,
                telegram_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error refreshing token for user {telegram_id}: {e}")
            return None
    
    return credentials


def has_google_credentials(telegram_id: int) -> bool:
    """Check if user has valid Google credentials"""
    return get_credentials(telegram_id) is not None


def revoke_credentials(telegram_id: int) -> bool:
    """Remove user's Google credentials"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM google_tokens WHERE telegram_id = ?', (telegram_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


# Initialize table on module load
init_google_tokens_table()
