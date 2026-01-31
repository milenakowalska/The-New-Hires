import os
import random
import asyncio
from google import genai
from sqlalchemy.future import select
from models import User, Message
from database import AsyncSessionLocal
from .socket_instance import sio
from .ai_utils import process_pr_link
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1beta'})


AI_TEAMMATES = [
    {"name": "Sarah", "role": "HR Manager", "style": "Friendly, welcoming, helpful, emojis", "github_id": "ai_sarah", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah"},
    {"name": "Mike", "role": "Senior Dev", "style": "Concise, technical, slightly cynical, helpful", "github_id": "ai_mike", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Mike"},
    {"name": "Alex", "role": "Full Stack Dev", "style": "Enthusiastic, asks questions, eager", "github_id": "ai_alex", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex"}
]

CONVERSATION_STARTERS = [
    "Ask them how their weekend was or tell a joke.",
    "Ask what they are working on today.",
    "Share a random fun fact about technology.",
    "Ask if they've seen any good movies recently.",
    "Complain jokingly about the coffee machine.",
    "Ask if they need help with anything.",
    "Tell a short, work-appropriate joke.",
    "Mention a trending tech topic like AI or quantum computing.",
    "Just say hello and wish them a productive day."
]

async def get_or_create_ai_user(db, teammate):
    # Lookup by username since github_id is removed
    stmt = select(User).where(User.username == teammate["name"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create AI user if not exists
        user = User(
            username=teammate["name"],
            avatar_url=teammate["avatar_url"],
            # No github_id or access_token needed for AI in new schema
            xp=1000,
            level=10,
            hashed_password="AI_BOT_NO_LOGIN" # Placeholder
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user

async def trigger_ai_response_task(channel: str, user_message: str):
    print(f"DEBUG AI: Triggered for channel={channel}, message='{user_message}'")
    # Random delay 2-5s
    await asyncio.sleep(random.randint(2, 5))
    
    if not GEMINI_API_KEY:
        print("Skipping AI response (No API Key)")
        return

    # 100% chance for MVP demonstration, random teammate
    
    try:
        async with AsyncSessionLocal() as db:
            # Picking a teammate early if needed for immediate feedback
            teammate = random.choice(AI_TEAMMATES)
            user = await get_or_create_ai_user(db, teammate)

            # SPECIAL HANDLING FOR CODE REVIEW
            content = None
            
            if channel == "code-review":
                if "github.com" in user_message and "/pull/" in user_message:
                    # Emit immediate feedback from THE SAME USER
                    immediate_data = {
                        "id": random.randint(100000, 999999), # Temporary ID
                        "channel": channel,
                        "content": f"Thanks! Give me a minute, I'll take a look at this PR for you. 🔍",
                        "sender_id": user.id,
                        "is_bot": True,
                        "timestamp": datetime.now().isoformat(),
                        "sender_name": user.username,
                        "sender_avatar": user.avatar_url
                    }
                    await sio.emit("new_message", immediate_data)
                    
                    # Extract URL and process
                    words = user_message.split()
                    for word in words:
                        if "github.com" in word and "/pull/" in word:
                            content = await process_pr_link(word)
                            break
                elif "review" in user_message.lower() and "pr" in user_message.lower():
                    content = "Sure! Paste the GitHub PR link comfortably here, and I'll do a quick review."

            if not content:
            
                channel_context = {
                "general": "You are hanging out in the #general channel. Keep it casual, fun, and broad. Answer in a general way.",
                "dev": "You are in the #dev channel. Be weirdly specific, technical, and use software engineering jargon. Assume everyone knows how to code.",
                "code-review": "You are in the #code-review channel. Be picky, ask critical questions, or ask for code reviews. Act like a senior engineer reviewing a junior's PR.",
                "random": "You are in the #random channel. Ignore work topics. Tell jokes, share random facts, or talk about conspiracy theories. Be funny and weird."
            }
            
                specific_context = channel_context.get(channel, "You are in a chat channel.")

                prompt = f"""
                Act as {teammate['name']}, a {teammate['role']} at a tech startup.
                Style: {teammate['style']}
                Context: {specific_context}
                
                A teammate just sent: "{user_message}"
                
                Respond to them. Keep it short (1-2 sentences).
                """
                
                # In a real environment, this might take time, so we already sent the "thanks" for PRs
                response = client.models.generate_content(model=MODEL, contents=prompt)
                content = response.text
            
            msg = Message(
                channel=channel,
                content=content,
                is_bot=True,
                sender_id=user.id
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
            
            data = {
                "id": msg.id,
                "channel": msg.channel,
                "content": msg.content,
                "sender_id": user.id,
                "is_bot": True,
                "timestamp": msg.timestamp.isoformat(),
                "sender_name": user.username,
                "sender_avatar": user.avatar_url
            }
            
            await sio.emit("new_message", data)
            print(f"DEBUG AI: Sent response: {data['content'][:50]}...")
            
    except Exception as e:
        print(f"Error in AI response: {e}")
        import traceback
        traceback.print_exc()

async def trigger_proactive_message(channel: str, prompt_context: str, user_name: str = "Teammate"):
    """Trigger an AI message without a user prompt (proactive)"""
    if not GEMINI_API_KEY:
        return

    # Random delay 2-5s to feel natural
    await asyncio.sleep(random.randint(2, 5))

    try:
        async with AsyncSessionLocal() as db:
            teammate = random.choice(AI_TEAMMATES)
            user = await get_or_create_ai_user(db, teammate)
            
            
            prompt = f"""
            Act as {teammate['name']}, a {teammate['role']} at a tech startup.
            Style: {teammate['style']}
            
            Context: {prompt_context}
            User involved: {user_name}
            
            Write a short message (1 sentence) to the channel or the user.
            """
            
            response = client.models.generate_content(model=MODEL, contents=prompt)
            content = response.text
            
            msg = Message(
                channel=channel,
                content=content,
                is_bot=True,
                sender_id=user.id
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
            
            data = {
                "id": msg.id,
                "channel": msg.channel,
                "content": msg.content,
                "sender_id": user.id,
                "is_bot": True,
                "timestamp": msg.timestamp.isoformat(),
                "sender_name": user.username,
                "sender_avatar": user.avatar_url
            }
            
            await sio.emit("new_message", data)
            
    except Exception as e:
        print(f"Error in proactive AI response: {e}")
