from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from database import get_db
from models import Ticket, TicketStatus, TicketPriority, User
from .gamification_utils import update_reliability
from datetime import datetime, timezone
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Valid status values
VALID_STATUSES = {"BACKLOG", "TODO", "IN_PROGRESS", "CODE_REVIEW", "IN_TEST", "PO_REVIEW", "DONE"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

class TicketCreate(BaseModel):
    title: str
    description: str
    type: str = "story"
    priority: str = "MEDIUM"
    story_points: int = 1
    due_date: Optional[datetime] = None
    
class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None

class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    type: str
    priority: str
    story_points: int
    status: str
    assignee_id: Optional[int]
    due_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

from .auth_utils import get_current_user

@router.get("/", response_model=List[TicketOut])
async def get_tickets(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Filter tickets by current logged in user
    stmt = select(Ticket).where(Ticket.assignee_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=TicketOut)
async def create_ticket(ticket: TicketCreate, db: AsyncSession = Depends(get_db)):
    db_ticket = Ticket(**ticket.dict())
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket

@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: int, ticket_update: TicketUpdate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    stmt = select(Ticket).options(selectinload(Ticket.assignee)).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    db_ticket = result.scalar_one_or_none()
    
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    update_data = ticket_update.dict(exclude_unset=True)
    
    # Validate status if provided
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}. Valid values: {VALID_STATUSES}")
        
        # Check if status is changing to DONE
        if new_status == "DONE" and db_ticket.status != "DONE":
            db_ticket.completed_at = datetime.now(timezone.utc)
            
            # Update Reliability
            if db_ticket.assignee:
                await update_reliability(db_ticket.assignee, db_ticket)

        # Effort: Moving to IN_PROGRESS or CODE_REVIEW
        from .gamification_utils import update_stat
        if new_status == "IN_PROGRESS" and db_ticket.status != "IN_PROGRESS":
            if db_ticket.assignee:
                await update_stat(db_ticket.assignee, "effort", 2)
        elif new_status == "CODE_REVIEW" and db_ticket.status != "CODE_REVIEW":
             if db_ticket.assignee:
                await update_stat(db_ticket.assignee, "effort", 1)

        # Log Activity
        if db_ticket.assignee:
            from .activity import log_activity
            from models import ActivityType
            
            activity_type = ActivityType.TICKET_STATUS_CHANGED
            description = f"Updated ticket '{db_ticket.title}' to {new_status}"
            
            # Special case for "sending for review"
            if new_status == "IN_TEST":
                activity_type = ActivityType.PULL_REQUEST_OPENED
                description = f"Submitted '{db_ticket.title}' for review"

            await log_activity(
                db,
                db_ticket.assignee.id,
                activity_type,
                description,
                {"ticket_id": db_ticket.id, "status": new_status, "title": db_ticket.title}
            )

    # Check for status change to IN_TEST
    if "status" in update_data and update_data["status"] == "IN_TEST":
        from .ai_chat import trigger_proactive_message
        username = db_ticket.assignee.username if db_ticket.assignee else "Teammate"
        background_tasks.add_task(
            trigger_proactive_message,
            "code-review",
            f"User {username} just moved ticket '{db_ticket.title}' to Testing/Review. Offer to help test or review.",
            username
        )
    
    # Validate priority if provided
    if "priority" in update_data:
        if update_data["priority"] not in VALID_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {update_data['priority']}")
    
    for key, value in update_data.items():
        setattr(db_ticket, key, value)
        
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket


