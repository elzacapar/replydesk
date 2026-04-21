import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

TONE_PRESETS = {
    "casual": (
        "You are a social media account owner replying to comments. "
        "Your tone is super casual and chill — like texting a friend. Use informal language, "
        "abbreviations are fine, be relaxed and fun. "
        "Always end with a short question or hook to invite a follow-up reply. "
        "Keep your reply to a maximum of 3 sentences. "
        "Do NOT use hashtags or marketing language."
    ),
    "professional": (
        "You are a social media account owner replying to comments. "
        "Your tone is polished and professional — knowledgeable, respectful, and clear. "
        "Be helpful and articulate without being stiff or corporate. "
        "Always end with a thoughtful question or invitation for further discussion. "
        "Keep your reply to a maximum of 3 sentences. "
        "Do NOT use hashtags, emojis, or marketing language."
    ),
    "witty": (
        "You are a social media account owner replying to comments. "
        "Your tone is clever and witty — use humor, wordplay, and playful sarcasm (never mean). "
        "Be entertaining and memorable while still being helpful. "
        "Always end with a funny question or clever hook to invite a follow-up reply. "
        "Keep your reply to a maximum of 3 sentences. "
        "Do NOT use hashtags or marketing language."
    ),
    "warm": (
        "You are a social media account owner replying to comments on your posts. "
        "Your tone is warm, genuine, and conversational — like a real person, not a brand. "
        "Be polite, a bit funny when the comment calls for it, and down-to-earth. "
        "Always end with a short question or hook to invite a follow-up reply. "
        "Keep your reply to a maximum of 3 sentences. "
        "Do NOT use hashtags, emojis excessively, or marketing language. "
        "Reply naturally as if you're chatting with a friend."
    ),
}

# Keyword-based negative sentiment detection
NEGATIVE_KEYWORDS = {
    "hate", "suck", "sucks", "terrible", "awful", "worst", "stupid", "idiot",
    "trash", "garbage", "disgusting", "pathetic", "loser", "fraud", "scam",
    "fake", "kys", "ugly", "dumb", "worthless", "useless", "cringe",
    "racist", "sexist", "die", "kill yourself", "go away", "unsubscribe",
    "dislike", "reported", "spam", "bot", "clickbait", "liar",
}


import re


def detect_sentiment(text):
    """Basic keyword-based sentiment detection with word-boundary matching. Returns 'negative' or 'positive'."""
    lower = text.lower()
    for kw in NEGATIVE_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return "negative"
    return "positive"


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def build_reply_prompt(comment_text, post_title="", post_description="", platform="", thread_history=None, tone_preset="warm"):
    context_parts = []
    if platform:
        context_parts.append(f"Platform: {platform}")
    if post_title:
        context_parts.append(f"Post/Video Title: {post_title}")
    if post_description:
        context_parts.append(f"Post/Video Description: {post_description}")
    
    thread_section = ""
    if thread_history and len(thread_history) > 0:
        thread_section = "\n\nThread history (oldest first):\n"
        for msg in thread_history:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")
            thread_section += f"- [{role}]: {text}\n"
        thread_section += f"\nNew message to reply to: {comment_text}"
    else:
        thread_section = f"\nComment to reply to: {comment_text}"
    
    context_str = "\n".join(context_parts)
    system_message = TONE_PRESETS.get(tone_preset, TONE_PRESETS["warm"])
    
    user_message = f"""Context:
{context_str}
{thread_section}

Write a reply:"""
    
    return system_message, user_message


async def generate_reply(comment_text, post_title="", post_description="", platform="", thread_history=None, tone_preset="warm"):
    client = get_groq_client()
    if not client:
        return "[Groq API key not configured. Add GROQ_API_KEY to your .env file.]"
    
    system_message, user_message = build_reply_prompt(
        comment_text, post_title, post_description, platform, thread_history, tone_preset
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.8,
            max_tokens=256,
            top_p=0.9,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return f"[Error generating reply: {str(e)}]"
