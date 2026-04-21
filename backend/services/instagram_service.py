import os
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

IG_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
IG_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
IG_API_BASE = "https://graph.facebook.com/v19.0"
SCOPES = "instagram_basic,instagram_manage_comments,pages_show_list,pages_read_engagement"


def get_credentials():
    app_id = os.environ.get("INSTAGRAM_APP_ID")
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET")
    return app_id, app_secret


def is_configured():
    aid, asec = get_credentials()
    return bool(aid and asec)


def get_auth_url(redirect_uri):
    app_id, _ = get_credentials()
    if not app_id:
        return None
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "response_type": "code",
    }
    return f"{IG_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code, redirect_uri):
    app_id, app_secret = get_credentials()
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    resp = requests.get(IG_TOKEN_URL, params=params)
    if resp.status_code != 200:
        logger.error(f"Instagram token exchange failed: {resp.text}")
        return None
    token_data = resp.json()
    
    # Exchange for long-lived token
    long_lived = requests.get(IG_TOKEN_URL, params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token_data["access_token"],
    })
    if long_lived.status_code == 200:
        token_data = long_lived.json()
    
    return token_data


async def get_ig_account_info(access_token):
    # Get pages first
    resp = requests.get(f"{IG_API_BASE}/me/accounts", params={
        "access_token": access_token,
        "fields": "id,instagram_business_account{id,name,username,profile_picture_url}",
    })
    if resp.status_code != 200:
        return None
    
    pages = resp.json().get("data", [])
    for page in pages:
        ig = page.get("instagram_business_account")
        if ig:
            return {
                "platform_user_id": ig["id"],
                "username": ig.get("username", ig.get("name", "")),
                "profile_image": ig.get("profile_picture_url", ""),
                "page_id": page["id"],
            }
    return None


async def fetch_comments(access_token, ig_user_id, replied_ids=None):
    if replied_ids is None:
        replied_ids = set()
    comments = []
    
    # Get recent media
    resp = requests.get(f"{IG_API_BASE}/{ig_user_id}/media", params={
        "access_token": access_token,
        "fields": "id,caption,timestamp",
        "limit": 20,
    })
    if resp.status_code != 200:
        logger.error(f"Instagram media fetch failed: {resp.text}")
        return comments
    
    media_items = resp.json().get("data", [])
    
    for media in media_items:
        media_id = media["id"]
        caption = media.get("caption", "")
        
        # Get comments for this media
        resp2 = requests.get(f"{IG_API_BASE}/{media_id}/comments", params={
            "access_token": access_token,
            "fields": "id,from,text,timestamp,replies{id,from,text,timestamp}",
            "limit": 50,
        })
        if resp2.status_code != 200:
            continue
        
        media_comments = resp2.json().get("data", [])
        for comment in media_comments:
            comment_id = comment["id"]
            if comment_id in replied_ids:
                replies = comment.get("replies", {}).get("data", [])
                for reply in replies:
                    reply_id = reply["id"]
                    if reply_id not in replied_ids and reply.get("from", {}).get("id") != ig_user_id:
                        thread_history = [
                            {"role": "commenter", "text": comment["text"]},
                        ]
                        for r in replies:
                            if r["id"] == reply_id:
                                break
                            role = "account" if r.get("from", {}).get("id") == ig_user_id else "commenter"
                            thread_history.append({"role": role, "text": r["text"]})
                        
                        comments.append({
                            "platform_comment_id": reply_id,
                            "parent_comment_id": comment_id,
                            "commenter_name": reply.get("from", {}).get("username", "Unknown"),
                            "commenter_avatar": "",
                            "comment_text": reply["text"],
                            "post_title": caption[:100] if caption else "Instagram Post",
                            "post_description": caption,
                            "post_id": media_id,
                            "thread_history": thread_history,
                            "is_thread_reply": True,
                        })
                continue
            
            if comment.get("from", {}).get("id") == ig_user_id:
                continue
            
            comments.append({
                "platform_comment_id": comment_id,
                "parent_comment_id": None,
                "commenter_name": comment.get("from", {}).get("username", "Unknown"),
                "commenter_avatar": "",
                "comment_text": comment["text"],
                "post_title": caption[:100] if caption else "Instagram Post",
                "post_description": caption,
                "post_id": media_id,
                "thread_history": None,
                "is_thread_reply": False,
            })
    
    return comments


async def post_reply(access_token, comment_id, reply_text):
    resp = requests.post(f"{IG_API_BASE}/{comment_id}/replies", params={
        "access_token": access_token,
        "message": reply_text,
    })
    if resp.status_code not in (200, 201):
        logger.error(f"Instagram post reply failed: {resp.text}")
        return False
    return True
