from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
import enum
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    avatar_url = Column(String)
    access_token = Column(String) # Encrypted
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    sprint_start_date = Column(DateTime(timezone=True), server_default=func.now())
    onboarding_completed_tasks = Column(MutableList.as_mutable(JSON), default=[])
    
    # RAG Indexing Metadata
    repo_full_name = Column(String, nullable=True) # e.g. "username/repo"
    last_indexed_commit = Column(String, nullable=True)
    
    # Gamification Stats
    truthfulness = Column(Integer, default=50)
    effort = Column(Integer, default=50)
    reliability = Column(Integer, default=50)
    collaboration = Column(Integer, default=50)
    quality = Column(Integer, default=50)
    
    messages = relationship("Message", back_populates="sender")
    tickets = relationship("Ticket", back_populates="assignee")
    standups = relationship("StandupSession", back_populates="user")
    reviews = relationship("CodeReview", back_populates="reviewer")
    achievements = relationship("Achievement", back_populates="user")
    retrospectives = relationship("Retrospective", back_populates="user")

class TicketStatus(str, enum.Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_TEST = "IN_TEST"
    PO_REVIEW = "PO_REVIEW"
    DONE = "DONE"

class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    type = Column(String, default="story")
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    story_points = Column(Integer, default=1)
    status = Column(Enum(TicketStatus), default=TicketStatus.BACKLOG)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    assignee = relationship("User", back_populates="tickets")

class Sprint(Base):
    __tablename__ = "sprints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, index=True)
    content = Column(Text)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Null for bot
    is_bot = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    sender = relationship("User", back_populates="messages")

class StandupSession(Base):
    __tablename__ = "standups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    audio_url = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())
    is_completed = Column(Boolean, default=True)

    user = relationship("User", back_populates="standups")

class CodeReview(Base):
    __tablename__ = "code_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    pr_number = Column(Integer)
    repo_name = Column(String)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Null for AI
    comments = Column(Text) # JSON structure stored as text
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviewer = relationship("User", back_populates="reviews")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(String)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="achievements")

class Retrospective(Base):
    __tablename__ = "retrospectives"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_url = Column(String)
    consent_given = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="retrospectives")

class ActivityType(str, enum.Enum):
    TICKET_ASSIGNED = "TICKET_ASSIGNED"
    TICKET_COMPLETED = "TICKET_COMPLETED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    REPO_CREATED = "REPO_CREATED"
    STANDUP_COMPLETED = "STANDUP_COMPLETED"
    RETROSPECTIVE_COMPLETED = "RETROSPECTIVE_COMPLETED"
    CODE_REVIEW_SUBMITTED = "CODE_REVIEW_SUBMITTED"
    ACHIEVEMENT_EARNED = "ACHIEVEMENT_EARNED"
    TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED"
    PULL_REQUEST_OPENED = "PULL_REQUEST_OPENED"

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(Enum(ActivityType))
    description = Column(String)
    extra_data = Column(Text, nullable=True)  # JSON data (renamed from metadata)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


