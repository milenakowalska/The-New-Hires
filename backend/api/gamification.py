from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from models import User, Achievement

router = APIRouter(prefix="/gamification", tags=["gamification"])

class UserStats(BaseModel):
    username: str
    level: int
    xp: int
    truthfulness: int = 50
    effort: int = 50
    reliability: int = 50
    collaboration: int = 50
    quality: int = 50
    avatar_url: Optional[str]

    class Config:
        from_attributes = True

@router.get("/leaderboard", response_model=List[UserStats])
async def get_leaderboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = select(User).order_by(User.xp.desc()).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users

@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    # In real app, user_id from auth
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user
