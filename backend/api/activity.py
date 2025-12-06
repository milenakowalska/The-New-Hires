from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from database import get_db
from models import Activity, ActivityType
from api.messages import sio
import json

router = APIRouter(prefix="/activity", tags=["activity"])

@router.get("/recent")
async def get_recent_activity(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity for a user"""
    stmt = select(Activity).where(
        Activity.user_id == user_id
    ).order_by(desc(Activity.created_at)).limit(limit)
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    return [
        {
            "id": activity.id,
            "type": activity.activity_type.value,
            "description": activity.description,
            "extra_data": json.loads(activity.extra_data) if activity.extra_data else {},
            "created_at": activity.created_at.isoformat()
        }
        for activity in activities
    ]

async def log_activity(
    db: AsyncSession,
    user_id: int,
    activity_type: ActivityType,
    description: str,
    extra_data: dict = None
):
    """Helper function to log user activity"""
    activity = Activity(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        extra_data=json.dumps(extra_data) if extra_data else None
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    # Emit real-time activity event
    await sio.emit("new_activity", {
        "id": activity.id,
        "user_id": user_id,
        "type": activity_type.value,
        "description": description,
        "extra_data": extra_data or {},
        "created_at": activity.created_at.isoformat()
    })
    
    return activity
