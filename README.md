# ReplyDesk

Social comment reply manager — fetch comments from YouTube, Instagram, Facebook, and TikTok, generate AI reply drafts with Groq, review and approve from one dashboard.

## Quick Start (Docker)

```bash
cp .env.example .env
# Fill in your API keys in .env
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8001

## Features

- Multi-platform support (YouTube, Instagram, Facebook, TikTok)
- AI-generated reply drafts via Groq (llama3-70b-8192)
- Per-account tone presets (Casual, Professional, Witty, Warm)
- Groq-based sentiment detection with auto-like for positive comments
- Sentiment override (toggle like/unlike per comment)
- Thread/reply tracking with full conversation history
- Review queue with Approve / Edit / Regenerate / Skip / Approve All
- OAuth 2.0 per platform with refresh token persistence

## Architecture

- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Database**: MongoDB 7 (Docker container)
- **AI**: Groq API (llama3-70b-8192)

## Environment Variables

See `.env.example` for all required keys. The app handles missing credentials gracefully — unconfigured platforms show a "Not connected" state.
