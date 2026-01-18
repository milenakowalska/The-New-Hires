from models import User, Ticket, TicketStatus, TicketPriority
import base64
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from typing import Optional

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class RepoRequest(BaseModel):
    project_description: str = "A simple todo app"
    repo_name: Optional[str] = None  # Auto-generated if not provided
    backend_stack: str = "Vanilla JS"
    frontend_stack: str = "Vanilla JS"

@router.post("/generate-repo")
async def generate_repository(request: RepoRequest, user_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Generate a repository with AI-generated code containing intentional bugs"""
    from sqlalchemy.future import select
    from .ai_utils import generate_project_with_bugs
    from .ai_chat import trigger_proactive_message
    
    # Fetch user to get token
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with GitHub")

    # Generate project with AI
    print(f"Generating project for: {request.project_description} (Backend: {request.backend_stack}, Frontend: {request.frontend_stack})")
    project = await generate_project_with_bugs(
        request.project_description, 
        backend_stack=request.backend_stack,
        frontend_stack=request.frontend_stack
    )
    
    # Use AI-generated repo name or provided one
    repo_name = request.repo_name or project.get("repo_name", "my-simulation-project")
    
    import httpx
    async with httpx.AsyncClient() as client:
        # Create Repo
        response = await client.post(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"token {user.access_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "name": repo_name,
                "private": False,
                "description": f"{project.get('project_name', 'Simulation')} - Generated for The New Hire",
                "auto_init": True
            }
        )
        
        if response.status_code not in [200, 201]:
            if response.status_code == 422:
                return {"message": "Repository already exists", "repo_url": f"https://github.com/{user.username}/{repo_name}"}
            print(f"GitHub Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to create repository")
            
        data = response.json()
        repo_url = data["html_url"]
        repo_full_name = f"{user.username}/{repo_name}"
        
        # Save repo info to user
        user.repo_full_name = repo_full_name
        await db.commit()
        
        # Helper function to push file to GitHub
        async def push_file(path: str, content: str, message: str):
            encoded = base64.b64encode(content.encode()).decode()
            result = await client.put(
                f"https://api.github.com/repos/{user.username}/{repo_name}/contents/{path}",
                headers={
                    "Authorization": f"token {user.access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "message": message,
                    "content": encoded
                }
            )
            return result
        
        # Push all generated files
        files = project.get("files", {})
        for filename, content in files.items():
            await push_file(filename, content, f"Add {filename}")
        
        # Push CI/CD workflow
        ci_content = """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint JavaScript
        run: echo "Linting JavaScript files..."
      - name: Run tests
        run: echo "Running tests..."
"""
        await push_file(".github/workflows/ci.yml", ci_content, "Add CI/CD workflow")
        
        # Create tickets from AI-generated list
        now = datetime.now()
        tickets_data = project.get("tickets", [])
        
        priority_map = {
            "CRITICAL": TicketPriority.CRITICAL,
            "HIGH": TicketPriority.HIGH,
            "MEDIUM": TicketPriority.MEDIUM,
            "LOW": TicketPriority.LOW
        }
        
        created_tickets = []
        for ticket_info in tickets_data:
            ticket = Ticket(
                title=ticket_info.get("title", "Untitled Task"),
                description=ticket_info.get("description", ""),
                type=ticket_info.get("type", "task"),
                priority=priority_map.get(ticket_info.get("priority", "MEDIUM").upper(), TicketPriority.MEDIUM),
                story_points=ticket_info.get("story_points", 2),
                status=TicketStatus.TODO if ticket_info.get("day", 1) <= 2 else TicketStatus.BACKLOG,
                assignee_id=user.id,
                due_date=now + timedelta(days=ticket_info.get("day", 3))
            )
            created_tickets.append(ticket)
        
        if created_tickets:
            db.add_all(created_tickets)
            await db.commit()
        
        background_tasks.add_task(
            trigger_proactive_message,
            "dev",
            f"The user just cloned their first repo: {repo_name}. Offer technical help if they get stuck.",
            user.username
        )

        # Trigger RAG indexing in background
        from .rag_utils import rag_engine
        background_tasks.add_task(
            rag_engine.index_files,
            user.id,
            repo_full_name,
            files
        )

        from .activity import log_activity
        from models import ActivityType
        await log_activity(
            db,
            user.id,
            ActivityType.REPO_CREATED,
            f"Created new GitHub repository: {repo_name}",
            {"repo_name": repo_name, "repo_url": repo_url}
        )

        # Reset onboarding checklist for the new project
        user.onboarding_completed_tasks = []
        user.onboarding_completed_tasks = list(user.onboarding_completed_tasks) # Force detection
        await db.commit()

        return {
            "message": f"Repository created with {len(files)} files and {len(created_tickets)} tickets!",
            "repo_url": repo_url,
            "project_name": project.get("project_name"),
            "tickets_created": len(created_tickets),
            "is_fallback": project.get("is_fallback", False)
        }

@router.get("/checklist")
async def get_onboarding_checklist(user_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch onboarding checklist with completion status for a specific user"""
    from sqlalchemy.future import select
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    completed_task_ids = user.onboarding_completed_tasks if user and user.onboarding_completed_tasks else []
    
    tasks = [
        {"id": 1, "task": "Clone the repository", "xp": 50},
        {"id": 2, "task": "Open the project in your editor", "xp": 25},
        {"id": 4, "task": "Find and fix your first bug", "xp": 100},
        {"id": 5, "task": "Commit your fix", "xp": 50},
        {"id": 6, "task": "Complete your first Standup", "xp": 50},
        {"id": 7, "task": "Submit a Pull Request", "xp": 100},
    ]
    
    for task in tasks:
        task["completed"] = task["id"] in completed_task_ids
        
    return tasks

class TaskCompletionRequest(BaseModel):
    task_id: int

@router.post("/complete-task")
async def complete_onboarding_task(request: TaskCompletionRequest, user_id: int, db: AsyncSession = Depends(get_db)):
    """Complete an onboarding task and award XP"""
    from sqlalchemy.future import select
    from .gamification_utils import award_xp
    from .activity import log_activity
    from models import ActivityType
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.onboarding_completed_tasks is None:
        user.onboarding_completed_tasks = []
        
    if request.task_id in user.onboarding_completed_tasks:
        return {"message": "Task already completed", "xp_awarded": 0}
        
    # Get XP value (hardcoded map for now to match checklist)
    xp_map = {1: 50, 2: 25, 3: 25, 4: 100, 5: 50, 6: 50, 7: 100}
    xp_to_award = xp_map.get(request.task_id, 0)
    
    user.onboarding_completed_tasks.append(request.task_id)
    # Using MutableList ensures SQLALchemy detects change, but we also re-assign to be sure
    user.onboarding_completed_tasks = list(user.onboarding_completed_tasks)
    
    await award_xp(user, xp_to_award)
    
    await log_activity(
        db,
        user.id,
        ActivityType.TICKET_COMPLETED, # Reusing activity type or could add new one
        f"Completed onboarding task #{request.task_id}",
        {"task_id": request.task_id, "xp_awarded": xp_to_award}
    )
    
    await db.commit()
    
    return {
        "message": "Task completed successfully",
        "xp_awarded": xp_to_award,
        "total_xp": user.xp,
        "level": user.level
    }
