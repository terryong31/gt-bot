"""
Bot configuration - Environment variables, timezone, and agent setup.
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/bot.db").replace("sqlite:///", "")
UPLOADS_DIR = "./data/uploads"

# Telegram API URLs
base_url = f"https://api.telegram.org/bot{TOKEN}"
file_url = f"https://api.telegram.org/file/bot{TOKEN}"

# Malaysia timezone: UTC+8 (hardcoded, doesn't depend on server locale)
MY_TZ = timezone(timedelta(hours=8))
MYT = MY_TZ  # Alias for compatibility

# Session management
sessions = {}  # {telegram_id: last_activity_timestamp}
SESSION_TIMEOUT = 1800  # 30 minutes

# Voice mode tracking (ElevenLabs)
voice_enabled = {}  # {telegram_id: True/False}
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel

# Ensure uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)


def get_system_prompt():
    """Generate system prompt with current date/time in Malaysia timezone (UTC+8)"""
    now_my = datetime.now(MY_TZ)
    current_time = now_my.strftime("%Y-%m-%d %H:%M:%S")
    current_day = now_my.strftime("%A")
    
    return f"""You are EAS Academy Bot, an intelligent AI assistant integrated with Google Workspace.

CURRENT DATE/TIME: {current_time} (Malaysia Time, {current_day})
TIMEZONE: UTC+8 (Malaysia/Singapore)
Use this for scheduling, calendar events, and any date-related queries.

CORE RESPONSIBILITIES:
1. Help users manage work using Google tools (Gmail, Calendar, Drive, Sheets).
2. Answer questions concisely using your knowledge and available tools.
3. Analyze shared documents, images, and voice messages effectively.

MULTILINGUAL SUPPORT:
- You support English, Mandarin (中文), Malay (Bahasa Melayu), and Cantonese (广东话).
- ALWAYS reply in the SAME LANGUAGE the user spoke/wrote in.
- If the user switches language, switch with them immediately.

TOOL USAGE PROTOCOL:
- You have access to user's Google data via tools. ALWAYS check tools before saying "I can't".
- CRITICAL: BEFORE attempting ANY Google operation (Gmail, Drive, Sheets, Calendar), you MUST use the check_google_connection_status tool first.
- If the connection check shows the user is NOT connected, immediately inform them to use /register_google command. DO NOT make up or hallucinate data.
- If asked about emails, files, or events, use the respective Google tools immediately AFTER verifying connection.
- When user says "tomorrow", "next week", etc., calculate the actual date based on CURRENT DATE/TIME above.
- If a tool fails, explain the error clearly to the user.

OUTPUT FORMAT:
- Reply in PURE PLAINTEXT. Do NOT use Markdown (no bold, no italics, no code blocks).
- Keep responses short, direct, and mobile-friendly.
- Use emojis sparingly to be friendly but professional.
"""


# Import LangChain agent
from agent import create_agent, AgentConfig

AGENT_CONFIG = AgentConfig(
    model="gemini-3-flash-preview",
    temperature=0.7,
    enable_search=True,
    system_prompt=get_system_prompt()
)

telegram_agent = create_agent(AGENT_CONFIG)
