# Google Workspace Telegram Bot with Admin Panel

AI-powered Telegram bot using Gemini with admin dashboard for user access control and chat logging.

## Features

- **AI Chat** - Powered by Gemini 3 Flash Preview
- **Google Workspace** - Gmail, Calendar, Drive, Sheets, Tasks, Meet integration
- **Voice Responses** - ElevenLabs TTS for short responses
- **Multimodal** - Text, images, documents, audio, video
- **Web Scraping** - Analyze URLs with Jina Reader
- **Multilingual** - English, 中文, Bahasa, 广东话
- **Access Control** - Invite code registration
- **Admin Dashboard** - Manage users and view logs

## Project Structure

```
telegram-bot/
├── main.py              # Entry point (~70 lines)
├── bot/                 # Core bot package
│   ├── config.py        # Environment, agent setup
│   ├── database.py      # DB operations
│   ├── telegram.py      # Telegram API helpers
│   ├── handlers.py      # Command handlers
│   └── processor.py     # Message processing
├── agent/               # LangChain agent
│   ├── llm.py           # LLM wrapper
│   ├── memory.py        # ChromaDB memory
│   └── google_tools.py  # Google Workspace tools
├── admin/               # Admin panel
│   ├── api/             # FastAPI backend
│   └── frontend/        # React frontend
└── docker/              # Docker files
    ├── Dockerfile       # Bot Dockerfile
    ├── Dockerfile.admin # Admin Dockerfile
    └── docker-compose.yml
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
cd admin/frontend && npm install

# Create .env file
cp .env.example .env
# Edit .env with your tokens

# Run bot
python main.py

# Run admin panel (separate terminal)
cd admin/api && uvicorn main:app --reload --port 8000
```

### Docker Deployment

```bash
# Build and run (from project root)
docker-compose -f docker/docker-compose.yml up -d --build

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Restart services
docker-compose -f docker/docker-compose.yml restart
```

## Environment Variables

| Variable                 | Description                        |
| ------------------------ | ---------------------------------- |
| `TELEGRAM_BOT_TOKEN`   | Telegram bot token from @BotFather |
| `GEMINI_API_KEY`       | Google AI API key                  |
| `JWT_SECRET`           | Random secret for JWT signing      |
| `ADMIN_USERNAME`       | Admin panel username               |
| `ADMIN_PASSWORD`       | Admin panel password               |
| `GOOGLE_CLIENT_ID`     | Google OAuth client ID             |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret         |
| `GOOGLE_REDIRECT_URI`  | OAuth callback URL                 |
| `ELEVENLABS_API_KEY`   | Optional: ElevenLabs TTS API key   |

## Bot Commands

| Command              | Description                          |
| -------------------- | ------------------------------------ |
| `/start`           | Welcome message & registration check |
| `/help`            | Show all commands                    |
| `/register CODE`   | Register with invite code            |
| `/register_google` | Connect Google account               |
| `/unlink_google`   | Disconnect Google account            |
| `/google_status`   | Check Google connection              |
| `/enable_voice`    | Enable voice responses               |
| `/disable_voice`   | Disable voice responses              |

## Usage

### For Users

1. Start chat with bot
2. Send `/start` to check registration
3. Use `/register CODE` with invite code from admin
4. Use `/register_google` to connect Google account
5. Start chatting!

### For Admins

1. Open `http://your-server:8080`
2. Login with admin credentials
3. Create invite codes in Invites page
4. Share codes with employees
5. Monitor chats in Logs page

## Tech Stack

- **Bot**: Python + google-genai + LangChain
- **Agent**: Gemini 3 Flash + function calling
- **Memory**: ChromaDB with Google Embeddings
- **Admin API**: FastAPI + SQLite
- **Admin UI**: React + TypeScript + Tailwind
- **Voice**: ElevenLabs TTS
- **Deployment**: Docker + GitHub Actions
