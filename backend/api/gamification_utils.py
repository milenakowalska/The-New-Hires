from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from .messages import sio # Import the socket server

async def update_stat(user: User, stat_name: str, change: int):
    """Safely updates a user stat, clamping between 0 and 100. Awards XP."""
    current_value = getattr(user, stat_name, 50)
    new_value = max(0, min(100, current_value + change))
    setattr(user, stat_name, new_value)
    
    # Award XP for positive actions
    if change > 0:
        xp_gain = change * 10 
        user.xp = (user.xp or 0) + xp_gain
        
        # Check Level Up
        new_level = 1 + (user.xp // 500)
        if new_level > (user.level or 1):
            user.level = new_level
            print(f"User {user.username} leveled up to {new_level}!")
            await sio.emit("level_up", {"level": new_level, "username": user.username})

    # Emit generic stats update
    await sio.emit("stats_update", {
        "user_id": user.id,
        "truthfulness": user.truthfulness,
        "effort": user.effort,
        "collaboration": user.collaboration,
        "reliability": user.reliability,
        "quality": user.quality,
        "xp": user.xp,
        "level": user.level
    })

async def calculate_truthfulness(user: User, standup_text: str, db: AsyncSession):
    """
    Analyzes truthfulness by comparing standup text roughly with recent activity.
    In a real app, this would query recent commits/tickets.
    For MVP, we check for keywords.
    """
    # Mock Logic
    text_lower = standup_text.lower()
    
    # If they mention "fixed" or "completed" but we don't verify it (mock), 
    # we might give them the benefit of the doubt or penalize if we had real data.
    # Here, let's just reward detail.
    
    if len(text_lower.split()) < 5:
        # Too short, likely hiding something?
        await update_stat(user, "truthfulness", -2)
    elif "stuck" in text_lower or "blocker" in text_lower:
        # Honest about problems
        await update_stat(user, "truthfulness", 1)
    else:
        # Default slight reward for doing it
        await update_stat(user, "truthfulness", 1)

async def update_effort_and_collaboration(user: User, event_type: str, payload: dict):
    """
    Updates Effort and Collaboration based on GitHub events.
    """
    if event_type == "push":
        # Effort: Commits pushed
        commits = payload.get("commits", [])
        effort_points = min(len(commits), 5) # Cap at 5 points per push
        await update_stat(user, "effort", effort_points)
        
    elif event_type == "pull_request":
        action = payload.get("action")
        if action == "opened":
            await update_stat(user, "effort", 2)
        elif action == "review_requested":
            # If I am the reviewer? (Complex to map for MVP)
            pass
            pass
    elif event_type == "pull_request_review":
        await update_stat(user, "collaboration", 5)
        
    elif event_type == "issue_comment":
        await update_stat(user, "collaboration", 1)

async def update_reliability(user: User, ticket):
    """
    Updates Reliability based on ticket completion time.
    """
    if not ticket.due_date:
        # Small reward for finishing any ticket
        await update_stat(user, "reliability", 1)
        return

    # Compare completion time vs due date
    # In naive datetime comparison, ensure both are timezone aware or both naive.
    # SQLAlchemy returns aware datetimes if configured, but let's be safe.
    from datetime import datetime
    
    # Check if late
    if ticket.completed_at > ticket.due_date:
        # Penalize
        print(f"Ticket {ticket.id} late. Penalizing reliability.")
        await update_stat(user, "reliability", -10)
    else:
        # Reward
        print(f"Ticket {ticket.id} on time. Rewarding reliability.")
        await update_stat(user, "reliability", 5)

async def update_quality(user: User, conclusion: str):
    """
    Updates Quality based on CI/CD workflow results.
    """
    if conclusion == "success":
        await update_stat(user, "quality", 5)
    elif conclusion == "failure":
        await update_stat(user, "quality", -10)
