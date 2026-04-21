# ReplyDesk

A unified social media comment management dashboard. ReplyDesk fetches unanswered comments from YouTube, Instagram, Facebook, and TikTok, generates context-aware AI reply drafts using Groq, and lets you review, edit, and approve replies from a single interface.

Built as a Dockerized full-stack application — one `docker-compose up` and you're running.

![ReplyDesk Dashboard](https://via.placeholder.com/1200x600/13131a/d4d4dc?text=ReplyDesk+Dashboard)

---

## Features

**Multi-Platform Comment Ingestion**
- Connects to YouTube, Instagram, Facebook, and TikTok via OAuth 2.0
- Fetches new unanswered comments across all connected accounts
- Tracks replied comment IDs — never fetches or replies twice
- Detects follow-up replies in existing threads and presents full conversation history

**AI-Powered Reply Drafts**
- Generates reply drafts using Groq API (`llama3-70b-8192`)
- Context-aware — receives video/post title, description, and thread history
- Per-account tone presets: Casual, Professional, Witty, Warm
- One-click regeneration for a fresh draft

**Sentiment Detection & Auto-Like**
- Groq-based sentiment classification (positive / neutral / negative)
- Automatically likes positive comments on fetch
- Skips liking negative or hateful comments
- Manual sentiment override — click to toggle like/unlike on any comment

**Review Queue**
- Approve — posts the reply via the platform's API
- Edit — modify the draft inline, then approve
- Regenerate — get a new AI draft with one click
- Skip — dismiss a comment from the queue
- Approve All — batch-approve every pending comment

**Dashboard**
- Left sidebar with platform/account navigation and tone selector
- Top bar with live stats: pending count, approved today, total accounts
- Thread history display with full conversation context
- Softened dark theme designed for extended use

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React 19, Tailwind CSS, Shadcn/UI   |
| Backend    | Python, FastAPI, Motor (async MongoDB) |
| Database   | MongoDB 7                           |
| AI         | Groq API (llama3-70b-8192)          |
| Auth       | OAuth 2.0 (Google, Meta, TikTok)    |
| Deployment | Docker Compose (3 containers)       |

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Groq API key](https://console.groq.com/keys) (free tier available)

### Setup

```bash
# Clone the repository
git clone https://github.com/elzacapar/replydesk.git
cd replydesk

# Create your environment file
cp .env.example .env

# Add your Groq API key to .env
# GROQ_API_KEY=gsk_your_key_here

# Start all services
docker-compose up --build
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001

Demo data (4 accounts, 8 comments with pre-written AI drafts) is auto-seeded on first launch.

---

## Screenshots

> Replace these placeholders with actual screenshots of your running instance.

| Dashboard | Comment Card | Tone Selector |
|-----------|-------------|---------------|
| ![Dashboard](https://via.placeholder.com/400x250/13131a/d4d4dc?text=Dashboard) | ![Comment](https://via.placeholder.com/400x250/13131a/d4d4dc?text=Comment+Card) | ![Tone](https://via.placeholder.com/400x250/13131a/d4d4dc?text=Tone+Selector) |

---

## Configuring OAuth Credentials

The app supports four platforms. Each requires its own OAuth credentials. Add them to your `.env` file — unconfigured platforms will show a "Not connected" state without crashing.

### YouTube

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **YouTube Data API v3**
4. Go to **APIs & Services > Credentials**
5. Create an **OAuth 2.0 Client ID** (Web application)
6. Add `http://localhost:8001/api/accounts/youtube/callback` as an authorized redirect URI
7. Copy the Client ID and Client Secret to your `.env`:
   ```
   YOUTUBE_CLIENT_ID=your_client_id
   YOUTUBE_CLIENT_SECRET=your_client_secret
   ```

### Facebook

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app (type: Business)
3. Add the **Facebook Login** product
4. Under **Facebook Login > Settings**, add `http://localhost:8001/api/accounts/facebook/callback` as a valid OAuth redirect URI
5. Go to **App Settings > Basic** for your App ID and App Secret
6. Required permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_engagement`, `pages_read_user_content`
7. Add to `.env`:
   ```
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```

### Instagram

Instagram uses the same Meta developer app as Facebook, but requires an Instagram Business or Creator account linked to a Facebook Page.

1. Use the same Meta app from the Facebook setup above
2. Add the **Instagram Graph API** product
3. Add `http://localhost:8001/api/accounts/instagram/callback` as a valid redirect URI
4. Required permissions: `instagram_basic`, `instagram_manage_comments`, `pages_show_list`, `pages_read_engagement`
5. Add to `.env`:
   ```
   INSTAGRAM_APP_ID=your_app_id
   INSTAGRAM_APP_SECRET=your_app_secret
   ```

### TikTok

1. Go to [TikTok for Developers](https://developers.tiktok.com/)
2. Create a new app
3. Add `http://localhost:8001/api/accounts/tiktok/callback` as a redirect URI
4. Request scopes: `user.info.basic`, `video.list`, `comment.list`, `comment.list.manage`
5. Add to `.env`:
   ```
   TIKTOK_CLIENT_KEY=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   ```

---

## Project Structure

```
replydesk/
├── docker-compose.yml          # 3 services: mongo, backend, frontend
├── .env.example                # Template for environment variables
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py               # FastAPI app — all API routes
│   └── services/
│       ├── groq_service.py     # AI reply generation + sentiment detection
│       ├── youtube_service.py  # YouTube Data API v3 integration
│       ├── facebook_service.py # Facebook Graph API integration
│       ├── instagram_service.py# Instagram Graph API integration
│       └── tiktok_service.py   # TikTok API integration
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.js
    ├── craco.config.js
    ├── public/
    │   └── index.html
    └── src/
        ├── App.js              # Main app with state management
        ├── App.css             # Global styles and animations
        ├── index.css           # Tailwind + CSS variables
        ├── components/
        │   ├── Sidebar.jsx     # Platform/account navigation + tone selector
        │   ├── TopBar.jsx      # Stats dashboard + global actions
        │   ├── CommentQueue.jsx# Comment list with staggered animation
        │   ├── CommentCard.jsx # Comment display + action buttons
        │   ├── ThreadHistory.jsx# Conversation thread display
        │   └── EmptyState.jsx  # Empty queue state
        └── components/ui/      # Shadcn/UI component library
```

## API Endpoints

| Method | Endpoint                              | Description                        |
|--------|---------------------------------------|------------------------------------|
| GET    | `/api/stats`                          | Global statistics                  |
| GET    | `/api/platforms`                      | Platforms with accounts and status |
| GET    | `/api/accounts`                       | List all connected accounts        |
| DELETE | `/api/accounts/:id`                   | Remove an account                  |
| PUT    | `/api/accounts/:id/tone`              | Update account tone preset         |
| GET    | `/api/accounts/:platform/auth-url`    | Start OAuth flow                   |
| GET    | `/api/accounts/:platform/callback`    | OAuth callback                     |
| GET    | `/api/comments`                       | Get comment queue (filterable)     |
| POST   | `/api/comments/fetch`                 | Fetch new comments from platforms  |
| POST   | `/api/comments/:id/approve`           | Approve and post reply             |
| POST   | `/api/comments/:id/regenerate`        | Regenerate AI draft                |
| PUT    | `/api/comments/:id/edit`              | Edit draft text                    |
| POST   | `/api/comments/:id/skip`              | Skip a comment                     |
| POST   | `/api/comments/:id/toggle-like`       | Toggle auto-like override          |
| POST   | `/api/comments/approve-all`           | Approve all pending comments       |

---

## License

MIT
