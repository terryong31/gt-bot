"""
Command handlers for GT-Bot.
"""

from .config import ELEVENLABS_API_KEY
from .database import is_user_registered, register_user, update_session, get_voice_enabled, set_voice_enabled
from .telegram import send_reply


def handle_command(message):
    """
    Handle bot commands. Returns True if command was handled, False otherwise.
    """
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    username = message["from"].get("username")
    first_name = message["from"].get("first_name")
    last_name = message["from"].get("last_name")
    text = message.get("text", "")
    
    # Handle /start command
    if text.startswith("/start"):
        is_allowed = is_user_registered(telegram_id)
        
        if is_allowed is None:
            welcome_msg = """👋 Welcome to GT-Bot!

❌ You're not registered yet.

To get started:
1️⃣ Ask your admin for an invite code
2️⃣ Use: /register YOUR_CODE

Once registered, you'll have access to:
• AI-powered chat assistant
• Gmail, Calendar, Drive, Sheets integration
• Voice message support
• Image & document analysis

Type /help for all available commands."""
            send_reply(chat_id, welcome_msg)
        elif is_allowed:
            update_session(telegram_id)
            welcome_msg = f"""✅ Welcome back, {first_name or 'there'}!

🤖 I'm your AI assistant integrated with Google Workspace.

📌 Quick Setup:
• /register_google - Connect your Google account
• /enable_voice - Get voice responses (under 30 words)

💡 What I can do:
• Read & send emails
• Manage calendar events  
• Access Drive & Sheets
• Analyze images & voice messages
• Answer questions in 4 languages

Type /help for all commands. Let's get started!"""
            send_reply(chat_id, welcome_msg)
        else:
            send_reply(chat_id, "⛔ Your access has been revoked. Please contact your admin.")
        return True
    
    # Handle /help command
    if text == "/help":
        help_msg = """📚 GT-Bot - Help Guide

🔧 SETUP COMMANDS:
/register CODE - Register with invite code
/register_google - Connect Google account
/unlink_google - Disconnect Google account
/google_status - Check Google connection

🎙️ VOICE MODE:
/enable_voice - Enable voice responses
/disable_voice - Disable voice responses
(Voice only plays for short responses under 30 words)

💼 WHAT I CAN DO:
• "Check my emails" - Search Gmail
• "Send email to john@..." - Compose & send
• "What events do I have today?" - Calendar
• "Create meeting tomorrow 3pm" - Schedule
• "List my Drive files" - Browse files
• "Read spreadsheet X" - Access Sheets
• "What's on this link?" - Analyze URLs

📎 Send me images, voice messages, or documents - I'll analyze them!

🌐 Languages: English, 中文, Bahasa, 广东话"""
        send_reply(chat_id, help_msg)
        return True
    
    # Handle /enable_voice command
    if text == "/enable_voice":
        if not ELEVENLABS_API_KEY:
            send_reply(chat_id, "❌ Voice feature is not configured. Contact admin.")
            return True
        set_voice_enabled(telegram_id, True)
        send_reply(chat_id, "🎙️ Voice mode enabled! I'll reply with voice messages for short responses (under 30 words).\n\nUse /disable_voice to turn off.")
        return True
    
    # Handle /disable_voice command
    if text == "/disable_voice":
        set_voice_enabled(telegram_id, False)
        send_reply(chat_id, "🔇 Voice mode disabled. I'll reply with text only.")
        return True
    
    # Handle /register_google command (MUST be before /register check!)
    if text == "/register_google":
        from agent.google_auth import get_auth_url, has_google_credentials
        
        # Check if already linked
        if has_google_credentials(telegram_id):
            send_reply(
                chat_id,
                "✅ Your Google account is already connected!\n\n"
                "You can use commands like:\n"
                "• 'Send an email to...'\n"
                "• 'What events do I have today?'\n"
                "• 'List my Drive files'\n\n"
                "Use /unlink_google to disconnect."
            )
            return True
        
        auth_url = get_auth_url(telegram_id)
        send_reply(
            chat_id, 
            f'🔗 <a href="{auth_url}">Click here to connect your Google account</a>\n\n'
            "After authorizing, you'll have access to Gmail, Calendar, Drive, and Sheets tools!",
            parse_mode="HTML"
        )
        return True
    
    # Handle /unlink_google command
    if text == "/unlink_google":
        from agent.google_auth import revoke_credentials
        if revoke_credentials(telegram_id):
            send_reply(chat_id, "✅ Your Google account has been unlinked.")
        else:
            send_reply(chat_id, "❌ Failed to unlink Google account or no account was linked.")
        return True
    
    # Handle /google_status command
    if text == "/google_status":
        from agent.google_auth import has_google_credentials
        linked = has_google_credentials(telegram_id)
        if linked:
            send_reply(chat_id, "✅ Your Google account is connected! You can use Google services.")
        else:
            send_reply(chat_id, "❌ No Google account linked. Use /register_google to connect.")
        return True
    
    # Handle /register command (invite code registration)
    if text.startswith("/register"):
        parts = text.split()
        if len(parts) < 2:
            send_reply(chat_id, "❌ Please provide an invite code.\nUsage: /register YOUR_CODE")
            return True
        
        invite_code = parts[1].upper()
        success, msg = register_user(telegram_id, username, first_name, last_name, invite_code)
        
        if success:
            update_session(telegram_id)
            send_reply(chat_id, f"✅ {msg}")
        else:
            send_reply(chat_id, f"❌ {msg}")
        return True
    
    # Not a command
    return False
