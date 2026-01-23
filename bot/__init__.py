"""
Bot package - GT-Bot core functionality.
"""

from .config import telegram_agent, AGENT_CONFIG, MY_TZ, voice_enabled
from .database import get_db, is_user_registered, register_user, update_session, is_session_valid, log_chat, now_myt
from .telegram import send_reply, send_voice_reply, edit_message, get_updates, get_file_path, download_file, save_media
from .handlers import handle_command
from .processor import process_message

__all__ = [
    'telegram_agent',
    'AGENT_CONFIG', 
    'MY_TZ',
    'voice_enabled',
    'get_db',
    'is_user_registered',
    'register_user',
    'update_session',
    'is_session_valid',
    'log_chat',
    'now_myt',
    'send_reply',
    'send_voice_reply',
    'edit_message',
    'get_updates',
    'get_file_path',
    'download_file',
    'save_media',
    'handle_command',
    'process_message',
]
