from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import StandupSession, Retrospective, User
from .gamification_utils import calculate_truthfulness
from .storage_utils import save_upload_file
from .ai_utils import generate_coworker_update, generate_voice, transcribe_audio
from typing import List
import random
import os

router = APIRouter(prefix="/features", tags=["features"])

@router.post("/standups/upload")
async def upload_standup(user_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Upload to local storage
    file_url = save_upload_file(file, f"standup_{user_id}_{file.filename}")
    
    # Transcribe
    file_path = os.path.join("static", f"standup_{user_id}_{file.filename}")
    transcript = await transcribe_audio(file_path)
    
    standup = StandupSession(user_id=user_id, audio_url=file_url) #, transcript=transcript)
    db.add(standup)
    
    # Update Truthfulness based on transcript
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        await calculate_truthfulness(user, transcript, db)
        
    await db.commit()
    return {"url": file_url, "transcript": transcript}

@router.get("/standups/daily-update")
async def get_coworker_update():
    coworkers = [
        {"name": "Sarah", "role": "Frontend Lead", "context": "debugging the CSS grid layout"},
        {"name": "Mike", "role": "Backend dev", "context": "optimizing database queries"},
        {"name": "Alex", "role": "DevOps", "context": "fixing the CI/CD pipeline"},
        {"name": "Emily", "role": "Product Manager", "context": "planning the next sprint"}
    ]
    coworker = random.choice(coworkers)
    
    # Generate text
    text = await generate_coworker_update(coworker["name"], coworker["role"], coworker["context"])
    
    # Generate audio
    audio_bytes = await generate_voice(text, coworker["name"])
    
    # Save audio temporarily - only if we got valid audio
    audio_url = None
    if audio_bytes and len(audio_bytes) > 0:
        filename = f"coworker_{coworker['name']}_{random.randint(1000,9999)}.mp3"
        filepath = os.path.join("static", filename)
        os.makedirs("static", exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        audio_url = f"http://localhost:8000/static/{filename}"
    else:
        # No audio available - frontend will show text only and skip button
        audio_url = ""
        
    return {
        "name": coworker["name"],
        "role": coworker["role"],
        "text": text,
        "audio_url": audio_url
    }

@router.post("/retrospectives/upload")
async def upload_retrospective(user_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Upload to local storage
    file_url = save_upload_file(file, f"retro_{user_id}_{file.filename}")
    
    retro = Retrospective(user_id=user_id, video_url=file_url, consent_given=True)
    db.add(retro)
    await db.commit()
    return {"url": file_url}

@router.get("/retrospectives/sprint-stats")
async def get_sprint_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get sprint stats for the retrospective dashboard"""
    from models import Ticket, TicketStatus
    
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return {"error": "User not found"}
    
    # Get tickets assigned to user
    ticket_stmt = select(Ticket).where(Ticket.assignee_id == user_id)
    ticket_result = await db.execute(ticket_stmt)
    tickets = ticket_result.scalars().all()
    
    total_tickets = len(tickets)
    completed_tickets = len([t for t in tickets if t.status == TicketStatus.DONE])
    in_progress_tickets = len([t for t in tickets if t.status == TicketStatus.IN_PROGRESS])
    todo_tickets = len([t for t in tickets if t.status == TicketStatus.TODO])
    
    # Calculate completion rate
    completion_rate = round((completed_tickets / total_tickets * 100) if total_tickets > 0 else 0)
    
    # Calculate story points
    total_story_points = sum(t.story_points for t in tickets)
    completed_story_points = sum(t.story_points for t in tickets if t.status == TicketStatus.DONE)
    
    # Get standups count
    standup_stmt = select(StandupSession).where(StandupSession.user_id == user_id)
    standup_result = await db.execute(standup_stmt)
    standups = standup_result.scalars().all()
    
    return {
        "user": {
            "username": user.username,
            "avatar_url": user.avatar_url,
            "level": user.level,
            "xp": user.xp
        },
        "metrics": {
            "truthfulness": user.truthfulness,
            "effort": user.effort,
            "reliability": user.reliability,
            "collaboration": user.collaboration,
            "quality": user.quality
        },
        "tickets": {
            "total": total_tickets,
            "completed": completed_tickets,
            "in_progress": in_progress_tickets,
            "todo": todo_tickets,
            "completion_rate": completion_rate
        },
        "story_points": {
            "total": total_story_points,
            "completed": completed_story_points
        },
        "standups_completed": len(standups),
        "sprint_days": 7
    }

