import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def build_reply_prompt(comment_text, post_title="", post_description="", platform="", thread_history=None):
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
    
    system_message = (
        "You are a social media account owner replying to comments on your posts. "
        "Your tone is warm, genuine, and conversational — like a real person, not a brand. "
        "Be polite, a bit funny when the comment calls for it, and down-to-earth. "
        "Always end with a short question or hook to invite a follow-up reply. "
        "Keep your reply to a maximum of 3 sentences. "
        "Do NOT use hashtags, emojis excessively, or marketing language. "
        "Reply naturally as if you're chatting with a friend."
    )
    
    user_message = f"""Context:
{context_str}
{thread_section}

Write a reply:"""
    
    return system_message, user_message


async def generate_reply(comment_text, post_title="", post_description="", platform="", thread_history=None):
    client = get_groq_client()
    if not client:
        return "[Groq API key not configured. Add GROQ_API_KEY to your .env file.]"
    
    system_message, user_message = build_reply_prompt(
        comment_text, post_title, post_description, platform, thread_history
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
