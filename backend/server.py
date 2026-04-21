from fastapi import FastAPI, APIRouter, Query, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from services.groq_service import generate_reply, detect_sentiment
from services import youtube_service, facebook_service, instagram_service, tiktok_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Pydantic Models ───
class AccountOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    platform: str
    username: str
    platform_user_id: str
    profile_image: str = ""
    is_connected: bool = True
    tone_preset: str = "warm"
    created_at: str = ""

class CommentOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    account_id: str
    platform: str
    account_username: str = ""
    platform_comment_id: str
    parent_comment_id: Optional[str] = None
    commenter_name: str
    commenter_avatar: str = ""
    comment_text: str
    post_title: str = ""
    post_description: str = ""
    post_id: str = ""
    ai_draft: str = ""
    status: str = "pending"
    thread_history: Optional[list] = None
    is_thread_reply: bool = False
    auto_liked: bool = False
    sentiment: str = ""
    created_at: str = ""
    approved_at: Optional[str] = None

class EditDraftRequest(BaseModel):
    draft: str

class TonePresetRequest(BaseModel):
    tone_preset: str

class StatsOut(BaseModel):
    total_pending: int = 0
    total_approved_today: int = 0
    total_accounts: int = 0
    total_skipped: int = 0

class PlatformStatus(BaseModel):
    platform: str
    configured: bool
    accounts: List[AccountOut] = []

# ─── Helper ───
def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ─── Routes ───

@api_router.get("/")
async def root():
    return {"message": "ReplyDesk API"}

@api_router.get("/stats", response_model=StatsOut)
async def get_stats():
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    total_pending = await db.comments.count_documents({"status": "pending"})
    total_approved_today = await db.comments.count_documents({
        "status": "approved",
        "approved_at": {"$gte": today_start}
    })
    total_accounts = await db.accounts.count_documents({})
    total_skipped = await db.comments.count_documents({"status": "skipped"})
    return StatsOut(
        total_pending=total_pending,
        total_approved_today=total_approved_today,
        total_accounts=total_accounts,
        total_skipped=total_skipped,
    )

@api_router.get("/platforms", response_model=List[PlatformStatus])
async def get_platforms():
    platforms = []
    for pname, svc in [("youtube", youtube_service), ("instagram", instagram_service), ("facebook", facebook_service), ("tiktok", tiktok_service)]:
        accounts_cursor = db.accounts.find({"platform": pname}, {"_id": 0})
        accounts = await accounts_cursor.to_list(100)
        platforms.append(PlatformStatus(
            platform=pname,
            configured=svc.is_configured(),
            accounts=[AccountOut(**a) for a in accounts],
        ))
    return platforms

@api_router.get("/accounts", response_model=List[AccountOut])
async def get_accounts(platform: Optional[str] = None):
    query = {}
    if platform:
        query["platform"] = platform
    accounts = await db.accounts.find(query, {"_id": 0}).to_list(100)
    return [AccountOut(**a) for a in accounts]

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    result = await db.accounts.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.comments.delete_many({"account_id": account_id})
    return {"success": True}

@api_router.put("/accounts/{account_id}/tone")
async def update_tone_preset(account_id: str, body: TonePresetRequest):
    valid_tones = ["casual", "professional", "witty", "warm"]
    if body.tone_preset not in valid_tones:
        raise HTTPException(status_code=400, detail=f"Invalid tone. Choose from: {valid_tones}")
    result = await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"tone_preset": body.tone_preset}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "tone_preset": body.tone_preset}

@api_router.get("/accounts/{platform}/auth-url")
async def get_auth_url(platform: str, request: Request):
    backend_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{backend_url}/api/accounts/{platform}/callback"
    
    svc_map = {
        "youtube": youtube_service,
        "instagram": instagram_service,
        "facebook": facebook_service,
        "tiktok": tiktok_service,
    }
    svc = svc_map.get(platform)
    if not svc:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
    
    if not svc.is_configured():
        raise HTTPException(status_code=400, detail=f"{platform} credentials not configured. Add them to .env file.")
    
    url = svc.get_auth_url(redirect_uri)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    return {"auth_url": url}

@api_router.get("/accounts/{platform}/callback")
async def oauth_callback(platform: str, request: Request, code: str = Query(...)):
    backend_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{backend_url}/api/accounts/{platform}/callback"
    frontend_url = os.environ.get("FRONTEND_URL", "")
    
    account_data = None
    
    if platform == "youtube":
        token_data = await youtube_service.exchange_code(code, redirect_uri)
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        channel_info = await youtube_service.get_channel_info(token_data["access_token"])
        if not channel_info:
            raise HTTPException(status_code=400, detail="Failed to get channel info")
        account_data = {
            "id": str(uuid.uuid4()),
            "platform": "youtube",
            "username": channel_info["username"],
            "platform_user_id": channel_info["platform_user_id"],
            "profile_image": channel_info.get("profile_image", ""),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "is_connected": True,
            "tone_preset": "warm",
            "created_at": now_iso(),
        }
    elif platform == "facebook":
        token_data = await facebook_service.exchange_code(code, redirect_uri)
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        pages = await facebook_service.get_pages(token_data["access_token"])
        if not pages:
            raise HTTPException(status_code=400, detail="No Facebook pages found")
        page = pages[0]
        account_data = {
            "id": str(uuid.uuid4()),
            "platform": "facebook",
            "username": page["name"],
            "platform_user_id": page["id"],
            "profile_image": page.get("picture", {}).get("data", {}).get("url", ""),
            "access_token": page.get("access_token", token_data["access_token"]),
            "refresh_token": "",
            "is_connected": True,
            "tone_preset": "warm",
            "created_at": now_iso(),
        }
    elif platform == "instagram":
        token_data = await instagram_service.exchange_code(code, redirect_uri)
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        ig_info = await instagram_service.get_ig_account_info(token_data["access_token"])
        if not ig_info:
            raise HTTPException(status_code=400, detail="No Instagram business account found")
        account_data = {
            "id": str(uuid.uuid4()),
            "platform": "instagram",
            "username": ig_info["username"],
            "platform_user_id": ig_info["platform_user_id"],
            "profile_image": ig_info.get("profile_image", ""),
            "access_token": token_data["access_token"],
            "refresh_token": "",
            "page_id": ig_info.get("page_id", ""),
            "is_connected": True,
            "tone_preset": "warm",
            "created_at": now_iso(),
        }
    elif platform == "tiktok":
        token_data = await tiktok_service.exchange_code(code, redirect_uri)
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        access_token = token_data.get("access_token", "")
        user_info = await tiktok_service.get_user_info(access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get TikTok user info")
        account_data = {
            "id": str(uuid.uuid4()),
            "platform": "tiktok",
            "username": user_info["username"],
            "platform_user_id": user_info["platform_user_id"],
            "profile_image": user_info.get("profile_image", ""),
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token", ""),
            "is_connected": True,
            "tone_preset": "warm",
            "created_at": now_iso(),
        }
    
    if account_data:
        existing = await db.accounts.find_one({
            "platform": platform,
            "platform_user_id": account_data["platform_user_id"],
        })
        if existing:
            await db.accounts.update_one(
                {"platform": platform, "platform_user_id": account_data["platform_user_id"]},
                {"$set": {
                    "access_token": account_data["access_token"],
                    "refresh_token": account_data.get("refresh_token", ""),
                    "is_connected": True,
                    "username": account_data["username"],
                    "profile_image": account_data.get("profile_image", ""),
                }}
            )
        else:
            await db.accounts.insert_one(account_data)
    
    if frontend_url:
        from starlette.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend_url}?connected={platform}")
    return {"success": True, "platform": platform, "username": account_data.get("username", "")}

@api_router.get("/comments", response_model=List[CommentOut])
async def get_comments(
    account_id: Optional[str] = None,
    status: Optional[str] = "pending",
    platform: Optional[str] = None,
):
    query = {}
    if account_id:
        query["account_id"] = account_id
    if status:
        query["status"] = status
    if platform:
        query["platform"] = platform
    comments = await db.comments.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [CommentOut(**c) for c in comments]

@api_router.post("/comments/fetch")
async def fetch_new_comments():
    accounts = await db.accounts.find({}, {"_id": 0}).to_list(100)
    total_new = 0
    errors = []
    
    for account in accounts:
        try:
            platform = account["platform"]
            account_id = account["id"]
            access_token = account.get("access_token", "")
            platform_user_id = account.get("platform_user_id", "")
            
            # Get already replied comment IDs for this account
            replied_cursor = db.comments.find(
                {"account_id": account_id, "status": {"$in": ["approved", "skipped"]}},
                {"platform_comment_id": 1, "_id": 0}
            )
            replied_docs = await replied_cursor.to_list(10000)
            replied_ids = {d["platform_comment_id"] for d in replied_docs}
            
            # Also check pending ones
            pending_cursor = db.comments.find(
                {"account_id": account_id, "status": "pending"},
                {"platform_comment_id": 1, "_id": 0}
            )
            pending_docs = await pending_cursor.to_list(10000)
            known_ids = replied_ids | {d["platform_comment_id"] for d in pending_docs}
            
            raw_comments = []
            if platform == "youtube":
                raw_comments = await youtube_service.fetch_comments(access_token, platform_user_id, known_ids)
            elif platform == "facebook":
                raw_comments = await facebook_service.fetch_comments(access_token, platform_user_id, known_ids)
            elif platform == "instagram":
                raw_comments = await instagram_service.fetch_comments(access_token, platform_user_id, known_ids)
            elif platform == "tiktok":
                raw_comments = await tiktok_service.fetch_comments(access_token, platform_user_id, known_ids)
            
            for rc in raw_comments:
                if rc["platform_comment_id"] in known_ids:
                    continue
                
                # Detect sentiment
                sentiment = await detect_sentiment(rc["comment_text"])
                auto_liked = sentiment == "positive"
                
                # Get account tone preset
                tone_preset = account.get("tone_preset", "warm")
                
                # Generate AI reply
                ai_draft = await generate_reply(
                    comment_text=rc["comment_text"],
                    post_title=rc.get("post_title", ""),
                    post_description=rc.get("post_description", ""),
                    platform=platform,
                    thread_history=rc.get("thread_history"),
                    tone_preset=tone_preset,
                )
                
                comment_doc = {
                    "id": str(uuid.uuid4()),
                    "account_id": account_id,
                    "platform": platform,
                    "account_username": account.get("username", ""),
                    "platform_comment_id": rc["platform_comment_id"],
                    "parent_comment_id": rc.get("parent_comment_id"),
                    "commenter_name": rc["commenter_name"],
                    "commenter_avatar": rc.get("commenter_avatar", ""),
                    "comment_text": rc["comment_text"],
                    "post_title": rc.get("post_title", ""),
                    "post_description": rc.get("post_description", ""),
                    "post_id": rc.get("post_id", ""),
                    "ai_draft": ai_draft,
                    "status": "pending",
                    "thread_history": rc.get("thread_history"),
                    "is_thread_reply": rc.get("is_thread_reply", False),
                    "auto_liked": auto_liked,
                    "sentiment": sentiment,
                    "created_at": now_iso(),
                    "approved_at": None,
                }
                await db.comments.insert_one(comment_doc)
                total_new += 1
        except Exception as e:
            logger.error(f"Error fetching comments for {account.get('username', 'unknown')}: {e}")
            errors.append(f"{account.get('platform', '?')}/{account.get('username', '?')}: {str(e)}")
    
    return {"total_new": total_new, "errors": errors}

@api_router.post("/comments/{comment_id}/approve")
async def approve_comment(comment_id: str):
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    account = await db.accounts.find_one({"id": comment["account_id"]}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Post the reply via platform API
    platform = comment["platform"]
    access_token = account.get("access_token", "")
    reply_text = comment["ai_draft"]
    posted = False
    
    try:
        if platform == "youtube":
            parent_id = comment.get("parent_comment_id") or comment["platform_comment_id"]
            posted = await youtube_service.post_reply(access_token, parent_id, reply_text)
        elif platform == "facebook":
            posted = await facebook_service.post_reply(access_token, comment["platform_comment_id"], reply_text)
        elif platform == "instagram":
            posted = await instagram_service.post_reply(access_token, comment["platform_comment_id"], reply_text)
        elif platform == "tiktok":
            posted = await tiktok_service.post_reply(access_token, comment.get("post_id", ""), comment["platform_comment_id"], reply_text)
    except Exception as e:
        logger.error(f"Error posting reply: {e}")
        # Still mark as approved in demo mode
    
    await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"status": "approved", "approved_at": now_iso()}}
    )
    return {"success": True, "posted_to_platform": posted}

@api_router.post("/comments/{comment_id}/regenerate")
async def regenerate_draft(comment_id: str):
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Get account's tone preset
    account = await db.accounts.find_one({"id": comment["account_id"]}, {"_id": 0})
    tone_preset = account.get("tone_preset", "warm") if account else "warm"
    
    new_draft = await generate_reply(
        comment_text=comment["comment_text"],
        post_title=comment.get("post_title", ""),
        post_description=comment.get("post_description", ""),
        platform=comment.get("platform", ""),
        thread_history=comment.get("thread_history"),
        tone_preset=tone_preset,
    )
    
    await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"ai_draft": new_draft}}
    )
    return {"success": True, "new_draft": new_draft}

@api_router.put("/comments/{comment_id}/edit")
async def edit_draft(comment_id: str, body: EditDraftRequest):
    result = await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"ai_draft": body.draft}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"success": True}

@api_router.post("/comments/{comment_id}/skip")
async def skip_comment(comment_id: str):
    result = await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"status": "skipped"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"success": True}

@api_router.post("/comments/{comment_id}/toggle-like")
async def toggle_like(comment_id: str):
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    new_liked = not comment.get("auto_liked", False)
    await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"auto_liked": new_liked}}
    )
    return {"success": True, "auto_liked": new_liked}

@api_router.post("/comments/approve-all")
async def approve_all_comments(account_id: Optional[str] = None):
    query = {"status": "pending"}
    if account_id:
        query["account_id"] = account_id
    
    pending = await db.comments.find(query, {"_id": 0}).to_list(500)
    approved_count = 0
    
    for comment in pending:
        account = await db.accounts.find_one({"id": comment["account_id"]}, {"_id": 0})
        if not account:
            continue
        
        platform = comment["platform"]
        access_token = account.get("access_token", "")
        reply_text = comment["ai_draft"]
        
        try:
            if platform == "youtube":
                parent_id = comment.get("parent_comment_id") or comment["platform_comment_id"]
                await youtube_service.post_reply(access_token, parent_id, reply_text)
            elif platform == "facebook":
                await facebook_service.post_reply(access_token, comment["platform_comment_id"], reply_text)
            elif platform == "instagram":
                await instagram_service.post_reply(access_token, comment["platform_comment_id"], reply_text)
            elif platform == "tiktok":
                await tiktok_service.post_reply(access_token, comment.get("post_id", ""), comment["platform_comment_id"], reply_text)
        except Exception as e:
            logger.error(f"Error posting reply: {e}")
        
        await db.comments.update_one(
            {"id": comment["id"]},
            {"$set": {"status": "approved", "approved_at": now_iso()}}
        )
        approved_count += 1
    
    return {"approved_count": approved_count}

# ─── Demo data seed ───
@api_router.post("/seed-demo")
async def seed_demo_data():
    demo_accounts = [
        {
            "id": "demo-yt-1",
            "platform": "youtube",
            "username": "TechVlogDaily",
            "platform_user_id": "UC_demo_yt_1",
            "profile_image": "",
            "access_token": "",
            "refresh_token": "",
            "is_connected": False,
            "tone_preset": "warm",
            "created_at": now_iso(),
        },
        {
            "id": "demo-ig-1",
            "platform": "instagram",
            "username": "travel.with.mia",
            "platform_user_id": "ig_demo_1",
            "profile_image": "",
            "access_token": "",
            "refresh_token": "",
            "is_connected": False,
            "tone_preset": "casual",
            "created_at": now_iso(),
        },
        {
            "id": "demo-fb-1",
            "platform": "facebook",
            "username": "LocalEats Chicago",
            "platform_user_id": "fb_demo_1",
            "profile_image": "",
            "access_token": "",
            "refresh_token": "",
            "is_connected": False,
            "tone_preset": "professional",
            "created_at": now_iso(),
        },
        {
            "id": "demo-tt-1",
            "platform": "tiktok",
            "username": "diy_dan",
            "platform_user_id": "tt_demo_1",
            "profile_image": "",
            "access_token": "",
            "refresh_token": "",
            "is_connected": False,
            "tone_preset": "witty",
            "created_at": now_iso(),
        },
    ]
    
    demo_comments = [
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-yt-1",
            "platform": "youtube",
            "account_username": "TechVlogDaily",
            "platform_comment_id": "yt_c_001",
            "parent_comment_id": None,
            "commenter_name": "Sarah K.",
            "commenter_avatar": "",
            "comment_text": "This camera comparison was so helpful! I've been going back and forth between these two for weeks. Which one do you personally use for travel?",
            "post_title": "Sony A7IV vs Canon R6 II - The REAL Difference",
            "post_description": "Full comparison of Sony A7IV and Canon R6 II for video creators",
            "post_id": "vid_001",
            "ai_draft": "So glad it helped you decide! Honestly, I grab the A7IV for travel because it's lighter and the autofocus is insane for run-and-gun. What kind of travel shooting are you planning?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-yt-1",
            "platform": "youtube",
            "account_username": "TechVlogDaily",
            "platform_comment_id": "yt_c_002",
            "parent_comment_id": None,
            "commenter_name": "Mike R.",
            "commenter_avatar": "",
            "comment_text": "You forgot to mention the battery life difference. That's a huge deal breaker for me.",
            "post_title": "Sony A7IV vs Canon R6 II - The REAL Difference",
            "post_description": "Full comparison of Sony A7IV and Canon R6 II for video creators",
            "post_id": "vid_001",
            "ai_draft": "Good catch, Mike! You're right, battery life is a big deal. The Canon does edge out slightly on a single charge. I'm doing a dedicated battery test video next week though, want me to tag you?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-yt-1",
            "platform": "youtube",
            "account_username": "TechVlogDaily",
            "platform_comment_id": "yt_c_003",
            "parent_comment_id": "yt_c_001",
            "commenter_name": "Sarah K.",
            "commenter_avatar": "",
            "comment_text": "Thanks for the reply! I'm going to Southeast Asia for 3 months. Mostly street photography and some video.",
            "post_title": "Sony A7IV vs Canon R6 II - The REAL Difference",
            "post_description": "Full comparison of Sony A7IV and Canon R6 II for video creators",
            "post_id": "vid_001",
            "ai_draft": "Southeast Asia for 3 months sounds amazing! For street photography the A7IV with a compact 35mm lens would be perfect — light and low-profile. Have you figured out your lens setup yet?",
            "status": "pending",
            "thread_history": [
                {"role": "commenter", "text": "This camera comparison was so helpful! I've been going back and forth between these two for weeks. Which one do you personally use for travel?"},
                {"role": "account", "text": "So glad it helped you decide! Honestly, I grab the A7IV for travel because it's lighter and the autofocus is insane for run-and-gun. What kind of travel shooting are you planning?"},
            ],
            "is_thread_reply": True,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-ig-1",
            "platform": "instagram",
            "account_username": "travel.with.mia",
            "platform_comment_id": "ig_c_001",
            "parent_comment_id": None,
            "commenter_name": "wanderlust_jake",
            "commenter_avatar": "",
            "comment_text": "This sunset is unreal!! Where exactly is this spot? I need to add it to my bucket list ASAP",
            "post_title": "Golden hour at Santorini never disappoints",
            "post_description": "Caught the most magical sunset from Oia castle viewpoint. The caldera views were absolutely breathtaking.",
            "post_id": "ig_post_001",
            "ai_draft": "It really was one of those pinch-me moments! This was taken right at the Oia Castle viewpoint — get there about an hour early though, it fills up fast. When are you thinking of visiting?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-ig-1",
            "platform": "instagram",
            "account_username": "travel.with.mia",
            "platform_comment_id": "ig_c_002",
            "parent_comment_id": None,
            "commenter_name": "photo.lisa",
            "commenter_avatar": "",
            "comment_text": "What camera settings did you use for this? The colors are incredible",
            "post_title": "Golden hour at Santorini never disappoints",
            "post_description": "Caught the most magical sunset from Oia castle viewpoint.",
            "post_id": "ig_post_001",
            "ai_draft": "Thank you so much Lisa! This was shot at f/2.8, 1/200s, ISO 100 — and honestly the light did most of the work. Do you shoot with a mirrorless or are you team phone photography?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-fb-1",
            "platform": "facebook",
            "account_username": "LocalEats Chicago",
            "platform_comment_id": "fb_c_001",
            "parent_comment_id": None,
            "commenter_name": "Jennifer Torres",
            "commenter_avatar": "",
            "comment_text": "We went there last weekend based on your recommendation and it was AMAZING! The deep dish was life-changing. Thank you!",
            "post_title": "Top 5 Deep Dish Pizza Spots You Haven't Tried Yet",
            "post_description": "Forget the tourist traps — these hidden gems serve the best deep dish in Chicago.",
            "post_id": "fb_post_001",
            "ai_draft": "So happy you loved it, Jennifer! Their deep dish really is on another level. Did you try the spinach and garlic one? That's my secret favorite that's not even on the main menu!",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-tt-1",
            "platform": "tiktok",
            "account_username": "diy_dan",
            "platform_comment_id": "tt_c_001",
            "parent_comment_id": None,
            "commenter_name": "craftqueen99",
            "commenter_avatar": "",
            "comment_text": "No way this only cost $50!! What wood did you use? I need to try this",
            "post_title": "I built a floating shelf for $50",
            "post_description": "Full tutorial on building a floating shelf from reclaimed wood",
            "post_id": "tt_vid_001",
            "ai_draft": "I know right?! I used reclaimed pine from a local salvage yard — that's the secret to keeping costs down. Are you planning to do just one shelf or a whole wall setup?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": "demo-tt-1",
            "platform": "tiktok",
            "account_username": "diy_dan",
            "platform_comment_id": "tt_c_002",
            "parent_comment_id": None,
            "commenter_name": "toolshed_tom",
            "commenter_avatar": "",
            "comment_text": "The joinery on this is clean. What saw are you using?",
            "post_title": "I built a floating shelf for $50",
            "post_description": "Full tutorial on building a floating shelf from reclaimed wood",
            "post_id": "tt_vid_001",
            "ai_draft": "Appreciate that, Tom! I'm using a DeWalt DWE7491RS table saw — it's a workhorse for the price. Been thinking about upgrading though, any recommendations from your setup?",
            "status": "pending",
            "thread_history": None,
            "is_thread_reply": False,
            "auto_liked": True,
            "sentiment": "positive",
            "created_at": now_iso(),
            "approved_at": None,
        },
    ]
    
    for acc in demo_accounts:
        await db.accounts.update_one(
            {"id": acc["id"]},
            {"$setOnInsert": acc},
            upsert=True,
        )
    for comm in demo_comments:
        await db.comments.update_one(
            {"platform_comment_id": comm["platform_comment_id"], "account_id": comm["account_id"]},
            {"$setOnInsert": comm},
            upsert=True,
        )
    
    return {"message": "Demo data seeded successfully", "seeded": True, "accounts": len(demo_accounts), "comments": len(demo_comments)}

@api_router.delete("/reset-demo")
async def reset_demo():
    await db.accounts.delete_many({"id": {"$regex": "^demo-"}})
    await db.comments.delete_many({"account_id": {"$regex": "^demo-"}})
    return {"message": "Demo data cleared"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def deduplicate_accounts():
    """Remove duplicate accounts on startup, keeping the first inserted."""
    pipeline = [
        {"$group": {"_id": "$id", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    async for group in db.accounts.aggregate(pipeline):
        # Keep first, delete the rest
        ids_to_delete = group["docs"][1:]
        await db.accounts.delete_many({"_id": {"$in": ids_to_delete}})
    logger.info("Startup: duplicate accounts cleaned")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
