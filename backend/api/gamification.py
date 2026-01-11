from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from database import get_db
from models import User, Achievement
from .socket_instance import sio

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

    model_config = ConfigDict(from_attributes=True)

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

@router.post("/sprint/reset")
async def reset_sprint(user_id: int, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
        
    user.sprint_start_date = datetime.now(timezone.utc)
    
    # Optionally reset tickets if they were closed? 
    # For now, just resetting the time counter as requested.
    
    await db.commit()

    # Notify frontend to refresh sprint data
    await sio.emit("sprint_updated", {"user_id": user_id, "current_day": 1})

    return {"message": "Sprint reset successfully", "new_start_date": user.sprint_start_date.isoformat()}
