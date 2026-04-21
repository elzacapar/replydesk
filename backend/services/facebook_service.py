import os
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

FB_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FB_API_BASE = "https://graph.facebook.com/v19.0"
SCOPES = "pages_show_list,pages_read_engagement,pages_manage_engagement,pages_read_user_content"


def get_credentials():
    app_id = os.environ.get("FACEBOOK_APP_ID")
    app_secret = os.environ.get("FACEBOOK_APP_SECRET")
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
    return f"{FB_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code, redirect_uri):
    app_id, app_secret = get_credentials()
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    resp = requests.get(FB_TOKEN_URL, params=params)
    if resp.status_code != 200:
        logger.error(f"Facebook token exchange failed: {resp.text}")
        return None
    token_data = resp.json()
    
    # Exchange for long-lived token
    long_lived = requests.get(FB_TOKEN_URL, params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token_data["access_token"],
    })
    if long_lived.status_code == 200:
        token_data = long_lived.json()
    
    return token_data


async def get_pages(access_token):
    resp = requests.get(f"{FB_API_BASE}/me/accounts", params={
        "access_token": access_token,
        "fields": "id,name,picture",
    })
    if resp.status_code != 200:
        return []
    return resp.json().get("data", [])


async def get_page_info(access_token):
    resp = requests.get(f"{FB_API_BASE}/me", params={
        "access_token": access_token,
        "fields": "id,name,picture",
    })
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "platform_user_id": data["id"],
        "username": data["name"],
        "profile_image": data.get("picture", {}).get("data", {}).get("url", ""),
    }


async def fetch_comments(page_access_token, page_id, replied_ids=None):
    if replied_ids is None:
        replied_ids = set()
    comments = []
    
    # Get recent posts
    resp = requests.get(f"{FB_API_BASE}/{page_id}/posts", params={
        "access_token": page_access_token,
        "fields": "id,message,created_time",
        "limit": 20,
    })
    if resp.status_code != 200:
        logger.error(f"Facebook posts fetch failed: {resp.text}")
        return comments
    
    posts = resp.json().get("data", [])
    
    for post in posts:
        post_id = post["id"]
        post_message = post.get("message", "")
        
        # Get comments for this post
        resp2 = requests.get(f"{FB_API_BASE}/{post_id}/comments", params={
            "access_token": page_access_token,
            "fields": "id,from,message,created_time,comments{id,from,message,created_time}",
            "limit": 50,
        })
        if resp2.status_code != 200:
            continue
        
        post_comments = resp2.json().get("data", [])
        for comment in post_comments:
            comment_id = comment["id"]
            if comment_id in replied_ids:
                # Check sub-comments for new replies
                sub_comments = comment.get("comments", {}).get("data", [])
                for sub in sub_comments:
                    sub_id = sub["id"]
                    if sub_id not in replied_ids and sub.get("from", {}).get("id") != page_id:
                        thread_history = [
                            {"role": "commenter", "text": comment["message"]},
                        ]
                        for s in sub_comments:
                            if s["id"] == sub_id:
                                break
                            role = "account" if s.get("from", {}).get("id") == page_id else "commenter"
                            thread_history.append({"role": role, "text": s["message"]})
                        
                        comments.append({
                            "platform_comment_id": sub_id,
                            "parent_comment_id": comment_id,
                            "commenter_name": sub.get("from", {}).get("name", "Unknown"),
                            "commenter_avatar": "",
                            "comment_text": sub["message"],
                            "post_title": post_message[:100] if post_message else "Facebook Post",
                            "post_description": post_message,
                            "post_id": post_id,
                            "thread_history": thread_history,
                            "is_thread_reply": True,
                        })
                continue
            
            if comment.get("from", {}).get("id") == page_id:
                continue
            
            comments.append({
                "platform_comment_id": comment_id,
                "parent_comment_id": None,
                "commenter_name": comment.get("from", {}).get("name", "Unknown"),
                "commenter_avatar": "",
                "comment_text": comment["message"],
                "post_title": post_message[:100] if post_message else "Facebook Post",
                "post_description": post_message,
                "post_id": post_id,
                "thread_history": None,
                "is_thread_reply": False,
            })
    
    return comments


async def post_reply(page_access_token, comment_id, reply_text):
    resp = requests.post(f"{FB_API_BASE}/{comment_id}/comments", params={
        "access_token": page_access_token,
        "message": reply_text,
    })
    if resp.status_code not in (200, 201):
        logger.error(f"Facebook post reply failed: {resp.text}")
        return False
    return True
