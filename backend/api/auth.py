from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from .ai_chat import trigger_proactive_message, CONVERSATION_STARTERS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User, Message
from .auth_utils import create_access_token, get_password_hash, verify_password, get_current_user
from .socket_instance import sio
import random
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        xp=0,
        level=1,
        avatar_url=None # Can be set later or use a default
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Send HR Welcome Message (Copied from old logic)
    await send_welcome_message(new_user, db)
    
    # Create JWT
    jwt_token = create_access_token({"sub": new_user.username, "id": new_user.id})
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "avatar_url": new_user.avatar_url,
            "level": new_user.level,
            "xp": new_user.xp
        }
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create JWT
    jwt_token = create_access_token({"sub": user.username, "id": user.id})
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "level": user.level,
            "xp": user.xp
        }
    }

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
        "level": current_user.level,
        "xp": current_user.xp
    }

async def send_welcome_message(user: User, db: AsyncSession):
    # Check if HR welcome message already exists for this user (just in case)
    welcome_check = await db.execute(
        select(Message).where(
            Message.channel == "general",
            Message.is_bot == True,
            Message.content.contains(f"Welcome to the team, **{user.username}**")
        )
    )
    existing_welcome = welcome_check.scalar_one_or_none()
    
    if not existing_welcome:
        # Create HR AI welcome message
        welcome_message = Message(
            channel="general",
            content=f"""👋 Welcome to the team, **{user.username}**!

I'm Sarah from HR, your AI onboarding assistant. We're excited to have you join us!

🚀 **Your first task:** Head over to the **Onboarding** page to generate your personal repository. This will set up your development environment and assign your first tasks.

Click on "Onboarding" in the sidebar to get started. Good luck with your first week!

_Remember: Your performance is being tracked from day one. Make it count!_ 💪""",
            sender_id=None,
            is_bot=True
        )
        db.add(welcome_message)
        await db.commit()
        await db.refresh(welcome_message)
        
        # Emit the welcome message via socket
        await sio.emit("new_message", {
            "id": welcome_message.id,
            "channel": welcome_message.channel,
            "content": welcome_message.content,
            "sender_id": None,
            "is_bot": True,
            "timestamp": welcome_message.timestamp.isoformat(),
            "sender_name": "Sarah (HR AI)",
            "sender_avatar": None
        })
