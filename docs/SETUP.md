# Quick Setup Guide

## 1. On Your VPS (ONE TIME SETUP)

SSH to your VPS and run these commands:

```bash
# Create project directory
sudo mkdir -p /opt/telegram-bot
sudo chown -R $USER:$USER /opt/telegram-bot
cd /opt/telegram-bot

# Create .env file
nano .env
```

Paste this (with YOUR tokens):
```
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
JWT_SECRET=random_secret_for_jwt
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/callback
ELEVENLABS_API_KEY=optional_for_voice_responses
```

Save: `Ctrl+X`, `Y`, `Enter`

**That's it for VPS setup!**

---

## 2. Add GitHub Secrets

Go to: `https://github.com/EASAcademy/telegram-bot/settings/secrets/actions`

Add these 4 secrets:
- `VPS_HOST` = your VPS IP
- `VPS_USER` = your SSH username
- `VPS_PASSWORD` = your SSH password  
- `GH_PAT` = your GitHub Personal Access Token

---

## 3. Deploy

Just push to main:
```bash
git push origin main
```

The bot will auto-deploy and run 24/7!

---

## Useful Commands on VPS

```bash
cd /opt/telegram-bot

# See if services are running
docker-compose -f docker/docker-compose.yml ps

# See logs
docker-compose -f docker/docker-compose.yml logs -f

# Restart services
docker-compose -f docker/docker-compose.yml restart

# Stop services
docker-compose -f docker/docker-compose.yml down

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Rebuild after code changes
docker-compose -f docker/docker-compose.yml up -d --build
```

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome + registration check |
| `/help` | Show all commands |
| `/register CODE` | Register with invite code |
| `/register_google` | Connect Google account |
| `/enable_voice` | Enable voice responses |
| `/disable_voice` | Disable voice responses |

**That's it. Simple.**
