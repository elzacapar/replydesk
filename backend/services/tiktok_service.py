import os
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

TT_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TT_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TT_API_BASE = "https://open.tiktokapis.com/v2"
SCOPES = "user.info.basic,video.list,comment.list,comment.list.manage"


def get_credentials():
    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    return client_key, client_secret


def is_configured():
    ck, cs = get_credentials()
    return bool(ck and cs)


def get_auth_url(redirect_uri):
    client_key, _ = get_credentials()
    if not client_key:
        return None
    params = {
        "client_key": client_key,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "response_type": "code",
    }
    return f"{TT_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code, redirect_uri):
    client_key, client_secret = get_credentials()
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(TT_TOKEN_URL, data=data)
    if resp.status_code != 200:
        logger.error(f"TikTok token exchange failed: {resp.text}")
        return None
    return resp.json()


async def refresh_access_token(refresh_token):
    client_key, client_secret = get_credentials()
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = requests.post(TT_TOKEN_URL, data=data)
    if resp.status_code != 200:
        logger.error(f"TikTok token refresh failed: {resp.text}")
        return None
    return resp.json()


async def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{TT_API_BASE}/user/info/", params={
        "fields": "open_id,display_name,avatar_url",
    }, headers=headers)
    if resp.status_code != 200:
        return None
    data = resp.json().get("data", {}).get("user", {})
    return {
        "platform_user_id": data.get("open_id", ""),
        "username": data.get("display_name", ""),
        "profile_image": data.get("avatar_url", ""),
    }


async def fetch_comments(access_token, user_id, replied_ids=None):
    if replied_ids is None:
        replied_ids = set()
    comments = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get user's videos
    resp = requests.post(f"{TT_API_BASE}/video/list/", json={
        "max_count": 20,
    }, headers=headers, params={"fields": "id,title,description"})
    
    if resp.status_code != 200:
        logger.error(f"TikTok video list failed: {resp.text}")
        return comments
    
    videos = resp.json().get("data", {}).get("videos", [])
    
    for video in videos:
        video_id = video.get("id", "")
        video_title = video.get("title", "")
        video_desc = video.get("description", "")
        
        # Get comments for video
        resp2 = requests.post(f"{TT_API_BASE}/comment/list/", json={
            "video_id": video_id,
            "max_count": 50,
        }, headers=headers, params={"fields": "id,text,create_time,user"})
        
        if resp2.status_code != 200:
            continue
        
        video_comments = resp2.json().get("data", {}).get("comments", [])
        for comment in video_comments:
            comment_id = comment.get("id", "")
            if comment_id in replied_ids:
                continue
            
            if comment.get("user", {}).get("open_id") == user_id:
                continue
            
            comments.append({
                "platform_comment_id": comment_id,
                "parent_comment_id": None,
                "commenter_name": comment.get("user", {}).get("display_name", "Unknown"),
                "commenter_avatar": comment.get("user", {}).get("avatar_url", ""),
                "comment_text": comment.get("text", ""),
                "post_title": video_title or video_desc[:100] or "TikTok Video",
                "post_description": video_desc,
                "post_id": video_id,
                "thread_history": None,
                "is_thread_reply": False,
            })
    
    return comments


async def post_reply(access_token, video_id, comment_id, reply_text):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.post(f"{TT_API_BASE}/comment/reply/", json={
        "video_id": video_id,
        "comment_id": comment_id,
        "text": reply_text,
    }, headers=headers)
    if resp.status_code not in (200, 201):
        logger.error(f"TikTok post reply failed: {resp.text}")
        return False
    return True
