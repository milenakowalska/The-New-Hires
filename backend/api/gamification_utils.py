from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from .socket_instance import sio # Import the socket server

async def award_xp(user: User, amount: int):
    """Directly awards XP and checks for level up."""
    if amount <= 0: return
    
    user.xp = (user.xp or 0) + amount
    
    # Check Level Up
    new_level = 1 + (user.xp // 100)
    if new_level > (user.level or 1):
        user.level = new_level
        print(f"User {user.username} leveled up to {new_level}!")
        await sio.emit("level_up", {"level": new_level, "username": user.username})

    # Emit generic stats update
    await sio.emit("stats_update", {
        "user_id": user.id,
        "xp": user.xp,
        "level": user.level,
        "truthfulness": user.truthfulness,
        "effort": user.effort,
        "collaboration": user.collaboration,
        "reliability": user.reliability,
        "quality": user.quality
    })

async def update_stat(user: User, stat_name: str, change: int):
    """Safely updates a user stat, clamping between 0 and 100. Awards XP."""
    current_value = getattr(user, stat_name, 50)
    new_value = max(0, min(100, current_value + change))
    setattr(user, stat_name, new_value)
    
    # Award XP for positive actions
    if change > 0:
        await award_xp(user, change * 10)
    else:
        # Just emit update if no XP change
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
    Analyzes truthfulness by comparing standup text with actual ticket status using AI.
    """
    from models import Ticket
    from sqlalchemy.future import select
    from .ai_utils import verify_standup_truthfulness
    
    # Fetch tickets assigned to user
    stmt = select(Ticket).where(Ticket.assignee_id == user.id)
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    
    # Format ticket summary for AI
    ticket_list = []
    for t in tickets:
        ticket_list.append(f"- [{t.status}] {t.title}")
    
    ticket_summary = "\n".join(ticket_list) if ticket_list else "No tickets assigned."
    
    # AI Verification
    verification = await verify_standup_truthfulness(standup_text, ticket_summary)
    
    score_change = verification.get("score", 0)
    reason = verification.get("explanation", "Verified by AI.")
    
    print(f"Truthfulness logic for {user.username}: {reason} (Score: {score_change})")
    await update_stat(user, "truthfulness", score_change)

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
    from datetime import datetime
    
    # Check if late
    completed = ticket.completed_at
    due = ticket.due_date

    # Make naive datetimes aware if needed (assuming local system time for naive)
    if completed and completed.tzinfo is None:
        completed = completed.astimezone()
    if due and due.tzinfo is None:
        due = due.astimezone()
        
    if completed > due:
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
