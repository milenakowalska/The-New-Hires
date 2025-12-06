from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db
from models import Message, User
from .socket_instance import sio

router = APIRouter(prefix="/messages", tags=["messages"])

class MessageCreate(BaseModel):
    channel: str
    content: str
    is_bot: bool = False

class MessageOut(BaseModel):
    id: int
    channel: str
    content: str
    sender_id: Optional[int]
    is_bot: bool
    timestamp: datetime
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/{channel}", response_model=List[MessageOut])
async def get_messages(channel: str, db: AsyncSession = Depends(get_db)):
    # Join with User to get sender details
    if channel not in ["general", "dev", "code-review"]:
         raise HTTPException(status_code=400, detail="Invalid channel")
         
    stmt = select(Message, User).outerjoin(User, Message.sender_id == User.id).where(Message.channel == channel).order_by(Message.timestamp.asc())
    result = await db.execute(stmt)
    
    messages = []
    for row in result:
        msg: Message = row[0]
        user: User = row[1]
        
        msg_out = MessageOut.from_orm(msg)
        if user:
            msg_out.sender_name = user.username
            msg_out.sender_avatar = user.avatar_url
        else:
            msg_out.sender_name = "Bot" if msg.is_bot else "Unknown"
            
        messages.append(msg_out)
        
    return messages

from .auth_utils import get_current_user
from .ai_chat import trigger_ai_response_task

@router.post("", response_model=MessageOut)
async def create_message(
    message: MessageCreate, 
    background_tasks: BackgroundTasks, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    db_message = Message(
        channel=message.channel,
        content=message.content,
        sender_id=current_user.id,
        is_bot=False
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    
    # Broadcast via Socket.IO
    msg_out = MessageOut.from_orm(db_message)
    msg_out.sender_name = current_user.username
    msg_out.sender_avatar = current_user.avatar_url
    
    data = msg_out.dict()
    # Serialize datetime
    data['timestamp'] = data['timestamp'].isoformat()
    
    await sio.emit("new_message", data)
    
    # Trigger AI response
    background_tasks.add_task(trigger_ai_response_task, message.channel, message.content)
    
    return db_message

# We will mount this in main.py
