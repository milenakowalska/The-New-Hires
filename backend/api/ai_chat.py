import os
import random
import asyncio
import openai
from sqlalchemy.future import select
from models import User, Message
from database import AsyncSessionLocal
from .socket_instance import sio
from datetime import datetime

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AI_TEAMMATES = [
    {"name": "Sarah", "role": "HR Manager", "style": "Friendly, welcoming, helpful, emojis", "github_id": "ai_sarah", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah"},
    {"name": "Mike", "role": "Senior Dev", "style": "Concise, technical, slightly cynical, helpful", "github_id": "ai_mike", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Mike"},
    {"name": "Alex", "role": "Full Stack Dev", "style": "Enthusiastic, asks questions, eager", "github_id": "ai_alex", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex"}
]

async def get_or_create_ai_user(db, teammate):
    stmt = select(User).where(User.github_id == teammate["github_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            github_id=teammate["github_id"],
            username=teammate["name"],
            avatar_url=teammate["avatar_url"],
            access_token="ai_token",
            xp=1000,
            level=10
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user

async def trigger_ai_response_task(channel: str, user_message: str):
    # Random delay 2-5s
    await asyncio.sleep(random.randint(2, 5))
    
    if not OPENAI_API_KEY:
        print("Skipping AI response (No API Key)")
        return

    # 100% chance for MVP demonstration, random teammate
    
    try:
        async with AsyncSessionLocal() as db:
            # Pick a teammate
            teammate = random.choice(AI_TEAMMATES)
            user = await get_or_create_ai_user(db, teammate)
            
            client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            
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
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            
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
        print(f"Error in AI response: {e}")

async def trigger_proactive_message(channel: str, prompt_context: str, user_name: str = "Teammate"):
    """Trigger an AI message without a user prompt (proactive)"""
    if not OPENAI_API_KEY:
        return

    # Random delay 2-5s to feel natural
    await asyncio.sleep(random.randint(2, 5))

    try:
        async with AsyncSessionLocal() as db:
            teammate = random.choice(AI_TEAMMATES)
            user = await get_or_create_ai_user(db, teammate)
            
            client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            prompt = f"""
            Act as {teammate['name']}, a {teammate['role']} at a tech startup.
            Style: {teammate['style']}
            
            Context: {prompt_context}
            User involved: {user_name}
            
            Write a short message (1 sentence) to the channel or the user.
            """
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            
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
