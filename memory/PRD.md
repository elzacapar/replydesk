# Social Comment Reply Manager - PRD

## Original Problem Statement
Build a Dockerized local web app that fetches unanswered comments from connected social accounts (YouTube, Instagram, Facebook, TikTok), generates AI reply drafts using Groq API (llama3-70b-8192), and populates a review queue per account/platform. Supports Approve, Regenerate, Edit, Skip, and Approve All actions. Dark theme, thread/reply tracking, OAuth flows per platform.

## Architecture
- **Backend**: FastAPI + MongoDB (motor async driver)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Database**: MongoDB
- **AI**: Groq API (llama3-70b-8192)
- **Docker**: docker-compose with 3 services (frontend, backend, mongo)

## User Personas
1. **Social Media Manager** - Manages multiple accounts across platforms, needs efficient comment reply workflow
2. **Content Creator** - Individual managing own channels, wants authentic quick replies
3. **Agency User** - Handles multiple client accounts, needs per-account filtering

## Core Requirements
- Multi-platform support: YouTube, Instagram, Facebook, TikTok
- OAuth 2.0 authentication per platform
- AI-generated reply drafts via Groq
- Review queue with Approve/Edit/Regenerate/Skip/Approve All
- Thread/reply tracking with conversation history context
- Graceful handling of missing API credentials
- Demo data seeding for testing

## What's Been Implemented (2026-04-21)
- Full FastAPI backend with all CRUD endpoints
- All 4 platform OAuth flows (YouTube, Instagram, Facebook, TikTok)
- Groq AI reply generation service
- React frontend with dark theme, sidebar, top bar, comment queue
- Comment cards with all actions (approve, edit, regenerate, skip)
- Thread history display
- Approve All functionality
- Demo data seeding
- Docker files (docker-compose.yml, Dockerfile, .env.example)

## DB Schema
### accounts collection
- id, platform, username, platform_user_id, profile_image, access_token, refresh_token, is_connected, created_at

### comments collection  
- id, account_id, platform, account_username, platform_comment_id, parent_comment_id, commenter_name, commenter_avatar, comment_text, post_title, post_description, post_id, ai_draft, status, thread_history, is_thread_reply, created_at, approved_at

## API Endpoints
- GET /api/stats - Global statistics
- GET /api/platforms - Platforms with accounts and config status
- GET /api/accounts - List accounts
- DELETE /api/accounts/{id} - Remove account
- GET /api/accounts/{platform}/auth-url - OAuth initiation
- GET /api/accounts/{platform}/callback - OAuth callback
- GET /api/comments - Comment queue with filters
- POST /api/comments/fetch - Fetch new comments
- POST /api/comments/{id}/approve - Approve and post
- POST /api/comments/{id}/regenerate - Regenerate AI draft
- PUT /api/comments/{id}/edit - Edit draft
- POST /api/comments/{id}/skip - Skip comment
- POST /api/comments/approve-all - Approve all
- POST /api/seed-demo - Seed demo data
- DELETE /api/reset-demo - Clear demo data

## Prioritized Backlog
### P0 (Critical - Done)
- [x] Backend API with all routes
- [x] Frontend with comment queue UI
- [x] Demo data seeding
- [x] Docker configuration files

### P1 (High Priority)
- [ ] Real OAuth testing with actual API keys
- [ ] Groq integration testing with real API key
- [ ] Comment fetching from live platforms
- [ ] Reply posting to live platforms
- [ ] Token refresh logic on expiry

### P2 (Medium Priority)
- [ ] Batch processing optimization
- [ ] Pagination for large comment queues
- [ ] Search/filter within comments
- [ ] Export approved replies as CSV
- [ ] Activity log/history view

### P3 (Nice to Have)
- [ ] Customizable AI tone settings
- [ ] Reply templates library
- [ ] Scheduling replies
- [ ] Analytics dashboard (engagement tracking)
- [ ] Multi-user access with roles
