from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import StandupSession, Retrospective, User
from .gamification_utils import calculate_truthfulness
from .storage_utils import save_upload_file
from .ai_utils import generate_coworker_update, generate_voice, transcribe_audio
from typing import List, Optional
from pydantic import BaseModel
import random
import os
import logging

logging.basicConfig(level=logging.INFO)
print("LOADING BACKEND/API/FEATURES.PY - IF YOU SEE THIS, THE CODE IS UPDATED")

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
        
        from .activity import log_activity
        from models import ActivityType
        await log_activity(
            db,
            user_id,
            ActivityType.STANDUP_COMPLETED,
            "Completed daily standup",
            {"transcript": transcript[:100] + "..." if len(transcript) > 100 else transcript}
        )
        
    await db.commit()
    return {"url": file_url, "transcript": transcript}

from fastapi import Response

@router.get("/standups/daily-update-v2")
async def get_coworker_update(response: Response):
    # Prevent browser caching of the standup update
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
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
        # Use absolute path to ensure we write to the correct static directory
        # Current file is backend/api/features.py
        # We want backend/static
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        static_dir = os.path.join(backend_dir, "static")
        
        os.makedirs(static_dir, exist_ok=True)
        
        import time
        filename = f"coworker_{coworker['name']}_{int(time.time())}.mp3"
        filepath = os.path.join(static_dir, filename)
        
        logging.info(f"DEBUG_LOG: Writing {len(audio_bytes)} bytes to {filepath}")
        
        try:
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
                f.flush()
                os.fsync(f.fileno())
            logging.info(f"DEBUG_LOG: File write complete. Exists? {os.path.exists(filepath)}")
            # Set permissions to be sure
            os.chmod(filepath, 0o644)
        except Exception as e:
            logging.error(f"DEBUG_LOG: Error writing file: {e}")
        
        # Ensure we return the correct URL for the static mount
        audio_url = f"http://localhost:8000/static/{filename}"
        logging.info(f"DEBUG_LOG: Returning URL {audio_url}")
        
    else:
        # No audio available - frontend will show text only and skip button
        audio_url = ""
        filepath = "N/A"
        
    return {
        "name": coworker["name"],
        "role": coworker["role"],
        "text": text,
        "audio_url": audio_url,
        "debug_path": filepath
    }

@router.post("/retrospectives/upload")
async def upload_retrospective(user_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Upload to local storage
    file_url = save_upload_file(file, f"retro_{user_id}_{file.filename}")
    
    retro = Retrospective(user_id=user_id, video_url=file_url, consent_given=True)
    db.add(retro)
    
    # Update Stats (Generic boost for retro)
    from .gamification_utils import update_stat
    from models import User
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        await update_stat(user, "collaboration", 5)
        
    # Log Activity
    from .activity import log_activity
    from models import ActivityType
    await log_activity(
        db,
        user_id,
        ActivityType.RETROSPECTIVE_COMPLETED,
        "Completed sprint retrospective",
        {"video_url": file_url}
    )
    
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
    completed_tickets = len([t for t in tickets if t.status == "DONE"])
    in_progress_tickets = len([t for t in tickets if t.status == "IN_PROGRESS"])
    todo_tickets = len([t for t in tickets if t.status == "TODO"])
    
    # Calculate completion rate
    completion_rate = round((completed_tickets / total_tickets * 100) if total_tickets > 0 else 0)
    
    # Calculate story points
    total_story_points = sum(t.story_points for t in tickets)
    completed_story_points = sum(t.story_points for t in tickets if t.status == "DONE")
    
    # Get standups count
    standup_stmt = select(StandupSession).where(StandupSession.user_id == user_id)
    standup_result = await db.execute(standup_stmt)
    standups = standup_result.scalars().all()
    
    # Calculate current day of sprint (1-7)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Ensure sprint_start_date is aware
    start_date = user.sprint_start_date
    if not start_date:
        start_date = now
        
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
        
    # Calculate days difference based on date (calendar days)
    diff = now.date() - start_date.date()
    sprint_day = diff.days + 1
    
    # Cap at 7 for display logic, or let frontend handle "Sprint Complete" state
    
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
        "sprint_days": 7,
        "current_day": sprint_day
    }

from .ai_utils import analyze_video

@router.post("/sprint-review/analyze")
async def analyze_sprint_review(user_id: int, duration: str = None, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Extract extension
    ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    if ext not in [".mp4", ".mov", ".webm"]:
        # Fallback to .mp4 if unknown, though frontend filters this
        pass

    # Upload to local storage temporarily
    filename = f"sprint_review_{user_id}_{int(time.time())}{ext}"
    file_url = save_upload_file(file, filename)
    
    # Absolute path for Gemini upload
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    file_path = os.path.join(backend_dir, "static", filename)
    
    try:
        # Analyze video
        report = await analyze_video(file_path, duration)
        
        # Log Activity
        from .activity import log_activity
        from models import ActivityType
        await log_activity(
            db,
            user_id,
            ActivityType.RETROSPECTIVE_COMPLETED,
            "Completed sprint review video analysis",
            {"report": report}
        )
        await db.commit()
        
        return {"report": report}
    finally:
        # Cleanup: delete the file after analysis as requested
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/sprint-review/history")
async def get_sprint_review_history(user_id: int, db: AsyncSession = Depends(get_db)):
    from models import Activity, ActivityType
    from sqlalchemy import desc
    import json
    
    stmt = select(Activity).where(
        Activity.user_id == user_id,
        Activity.activity_type == ActivityType.RETROSPECTIVE_COMPLETED
    ).order_by(desc(Activity.created_at))
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    history = []
    for activity in activities:
        if activity.extra_data:
            try:
                data = json.loads(activity.extra_data)
                if "report" in data:
                    history.append({
                        "date": activity.created_at.isoformat(),
                        "report": data["report"]
                    })
            except:
                continue
    
    return history

class SeniorColleagueChatRequest(BaseModel):
    message: str

@router.post("/senior-colleague/chat")
async def chat_with_senior_colleague(user_id: int, request: SeniorColleagueChatRequest, db: AsyncSession = Depends(get_db)):
    from models import User
    from .rag_utils import rag_engine
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.repo_full_name:
        return {"response": "I don't see a repository linked to your account. Have you completed onboarding yet?"}
        
    response = await rag_engine.query(user_id, user.repo_full_name, request.message)
    return {"response": response}

@router.post("/senior-colleague/sync")
async def sync_senior_colleague(user_id: int, db: AsyncSession = Depends(get_db)):
    from models import User
    from .rag_utils import rag_engine
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.repo_full_name or not user.access_token:
         return {"success": False, "message": "Missing repository or access token"}
         
    success = await rag_engine.sync_with_github(user_id, user.repo_full_name, user.access_token, db)
    return {"success": success}

import time

