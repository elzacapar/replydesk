import os
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
SCOPES = "https://www.googleapis.com/auth/youtube.force-ssl"


def get_credentials():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    return client_id, client_secret


def is_configured():
    cid, csec = get_credentials()
    return bool(cid and csec)


def get_auth_url(redirect_uri):
    client_id, _ = get_credentials()
    if not client_id:
        return None
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{YOUTUBE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code, redirect_uri):
    client_id, client_secret = get_credentials()
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post(YOUTUBE_TOKEN_URL, data=data)
    if resp.status_code != 200:
        logger.error(f"YouTube token exchange failed: {resp.text}")
        return None
    return resp.json()


async def refresh_access_token(refresh_token):
    client_id, client_secret = get_credentials()
    data = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }
    resp = requests.post(YOUTUBE_TOKEN_URL, data=data)
    if resp.status_code != 200:
        logger.error(f"YouTube token refresh failed: {resp.text}")
        return None
    return resp.json()


async def get_channel_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(
        f"{YOUTUBE_API_BASE}/channels",
        params={"part": "snippet", "mine": "true"},
        headers=headers,
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get("items"):
        ch = data["items"][0]
        return {
            "platform_user_id": ch["id"],
            "username": ch["snippet"]["title"],
            "profile_image": ch["snippet"]["thumbnails"]["default"]["url"],
        }
    return None


async def fetch_comments(access_token, channel_id, replied_ids=None):
    if replied_ids is None:
        replied_ids = set()
    headers = {"Authorization": f"Bearer {access_token}"}
    comments = []
    
    # Get all videos from the channel
    resp = requests.get(
        f"{YOUTUBE_API_BASE}/search",
        params={
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": 20,
        },
        headers=headers,
    )
    if resp.status_code != 200:
        logger.error(f"YouTube search failed: {resp.text}")
        return comments
    
    videos = resp.json().get("items", [])
    
    for video in videos:
        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]
        video_desc = video["snippet"].get("description", "")
        
        # Get comment threads for this video
        resp2 = requests.get(
            f"{YOUTUBE_API_BASE}/commentThreads",
            params={
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": 50,
                "order": "time",
            },
            headers=headers,
        )
        if resp2.status_code != 200:
            continue
        
        threads = resp2.json().get("items", [])
        for thread in threads:
            top_comment = thread["snippet"]["topLevelComment"]
            comment_id = top_comment["id"]
            
            if comment_id in replied_ids:
                # Check for new replies in existing threads
                replies = thread.get("replies", {}).get("comments", [])
                for reply in replies:
                    reply_id = reply["id"]
                    if reply_id not in replied_ids and reply["snippet"]["authorChannelId"]["value"] != channel_id:
                        thread_history = [
                            {"role": "commenter", "text": top_comment["snippet"]["textDisplay"]},
                        ]
                        for r in replies:
                            if r["id"] == reply_id:
                                break
                            role = "account" if r["snippet"]["authorChannelId"]["value"] == channel_id else "commenter"
                            thread_history.append({"role": role, "text": r["snippet"]["textDisplay"]})
                        
                        comments.append({
                            "platform_comment_id": reply_id,
                            "parent_comment_id": comment_id,
                            "commenter_name": reply["snippet"]["authorDisplayName"],
                            "commenter_avatar": reply["snippet"].get("authorProfileImageUrl", ""),
                            "comment_text": reply["snippet"]["textDisplay"],
                            "post_title": video_title,
                            "post_description": video_desc,
                            "post_id": video_id,
                            "thread_history": thread_history,
                            "is_thread_reply": True,
                        })
                continue
            
            # New top-level comment
            if top_comment["snippet"].get("authorChannelId", {}).get("value") == channel_id:
                continue
            
            comments.append({
                "platform_comment_id": comment_id,
                "parent_comment_id": None,
                "commenter_name": top_comment["snippet"]["authorDisplayName"],
                "commenter_avatar": top_comment["snippet"].get("authorProfileImageUrl", ""),
                "comment_text": top_comment["snippet"]["textDisplay"],
                "post_title": video_title,
                "post_description": video_desc,
                "post_id": video_id,
                "thread_history": None,
                "is_thread_reply": False,
            })
    
    return comments


async def post_reply(access_token, parent_id, reply_text):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "snippet": {
            "parentId": parent_id,
            "textOriginal": reply_text,
        }
    }
    resp = requests.post(
        f"{YOUTUBE_API_BASE}/comments",
        params={"part": "snippet"},
        headers=headers,
        json=data,
    )
    if resp.status_code not in (200, 201):
        logger.error(f"YouTube post reply failed: {resp.text}")
        return False
    return True
