# Docker CI/CD Deployment Guide

## Overview

Your bot now deploys automatically using **GitHub Actions + Docker** to your Hostinger VPS.

## What Happens on Push

When you push to `main`:

1. ✅ GitHub Actions connects to your VPS
2. ✅ Pulls latest code
3. ✅ Stops old Docker containers
4. ✅ Builds new Docker images
5. ✅ Runs new containers with auto-restart
6. ✅ Configures Nginx + SSL
7. ✅ Cleans up old images

## Project Structure

```
telegram-bot/
├── main.py              # Entry point
├── bot/                 # Core bot package
│   ├── config.py        # Environment, agent setup
│   ├── database.py      # DB operations
│   ├── telegram.py      # Telegram API helpers
│   ├── handlers.py      # Command handlers
│   └── processor.py     # Message processing
├── agent/               # LangChain agent
├── admin/               # Admin panel (API + Frontend)
└── docker/              # Docker files
    ├── Dockerfile       # Bot container
    ├── Dockerfile.admin # Admin container
    └── docker-compose.yml
```

## Required Setup

### 1. GitHub Secrets

Add these in **GitHub Settings → Secrets and variables → Actions**:

| Secret           | Description           | Example              |
| ---------------- | --------------------- | -------------------- |
| `VPS_HOST`     | VPS IP/hostname       | `123.45.67.89`     |
| `VPS_USER`     | SSH username          | `ubuntu`           |
| `VPS_PASSWORD` | SSH password          | `your-password`    |
| `GH_PAT`       | Personal Access Token | `ghp_xxxxxxxxxxxx` |

### 2. VPS Prerequisites

SSH into your VPS and install Docker:

```bash
# SSH to VPS
ssh root@your-vps-host

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. Create .env File on VPS

```bash
# Create project directory
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot

# Create .env file
nano .env
```

Add these lines:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=random_secret_string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/callback
ELEVENLABS_API_KEY=optional_for_voice
```

Save: `Ctrl+X`, then `Y`, then `Enter`

## Deploy Now

```bash
git add .
git commit -m "Deploy changes"
git push origin main
```

Watch deployment at: `https://github.com/{your-github-username}/gt-bot/actions`

## Manual Commands on VPS

```bash
cd /opt/telegram-bot

# View running containers
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Restart services
docker-compose -f docker/docker-compose.yml restart

# Stop services
docker-compose -f docker/docker-compose.yml down

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Rebuild and deploy
docker-compose -f docker/docker-compose.yml up -d --build
```

## Troubleshooting

**Container keeps restarting?**

```bash
docker-compose -f docker/docker-compose.yml logs telegram-bot
```

**Need to rebuild manually?**

```bash
cd /opt/telegram-bot
git pull origin main
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d --build
```

**Check if .env is correct:**

```bash
cat /opt/telegram-bot/.env
```
