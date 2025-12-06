from models import User, Ticket, TicketStatus, TicketPriority
import asyncio
import base64
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class RepoRequest(BaseModel):
    repo_name: str = "the-new-hire-simulation"

@router.post("/generate-repo")
async def generate_repository(request: RepoRequest, user_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch user to get token
    from sqlalchemy.future import select
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with GitHub")

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
                "name": request.repo_name,
                "private": False, # Public for now so we can see it easily
                "description": "Simulation Repository for The New Hire",
                "auto_init": True # Initialize with README
            }
        )
        
        if response.status_code not in [200, 201]:
             # If it exists, maybe just return the URL?
             if response.status_code == 422: # Already exists usually
                 return {"message": "Repository already exists", "repo_url": f"https://github.com/{user.username}/{request.repo_name}"}
                 
             print(f"GitHub Error: {response.text}")
             raise HTTPException(status_code=response.status_code, detail="Failed to create repository")
             
        data = response.json()
        repo_url = data["html_url"]
        
        # INJECT CI/CD WORKFLOW
        # We need to PUT to /repos/{owner}/{repo}/contents/{path}
        ci_content = """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run a one-line script
        run: echo Hello, world!
      - name: Run a multi-line script
        run: |
          echo Add other actions to build,
          echo test, and deploy your project.
"""
        # Encode content
        encoded_content = base64.b64encode(ci_content.encode()).decode()
        
        await client.put(
            f"https://api.github.com/repos/{user.username}/{request.repo_name}/contents/.github/workflows/ci.yml",
            headers={
                "Authorization": f"token {user.access_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "message": "Add CI/CD workflow (Auto-generated)",
                "content": encoded_content
            }
        )
        
        # SEED INITIAL TICKETS
        now = datetime.now()
        seed_tickets = [
            Ticket(
                title="Fix Critical Login Bug", 
                description="Users getting 500 error on login page.", 
                type="bug",
                priority=TicketPriority.CRITICAL,
                story_points=5,
                status=TicketStatus.TODO,
                assignee_id=user.id,
                due_date=now + timedelta(days=1)
            ),
             Ticket(
                title="Implement Dark Mode", 
                description="Add dark mode toggle to settings.", 
                type="story",
                priority=TicketPriority.MEDIUM,
                story_points=3,
                status=TicketStatus.BACKLOG,
                assignee_id=user.id,
                due_date=now + timedelta(days=3)
            ),
            Ticket(
                title="Update README.md", 
                description="Document installation steps.", 
                type="task",
                priority=TicketPriority.LOW,
                story_points=1,
                status=TicketStatus.TODO,
                assignee_id=user.id,
                due_date=now + timedelta(hours=5) 
            ),
             Ticket(
                title="Refactor API Utils", 
                description="Clean up the messy code in utils.py", 
                type="chore",
                priority=TicketPriority.HIGH,
                story_points=2,
                status=TicketStatus.BACKLOG,
                assignee_id=user.id,
                due_date=now + timedelta(days=2)
            ),
        ]
        
        db.add_all(seed_tickets)
        await db.commit()
        
        return {"message": "Repository created and seeded successfully", "repo_url": repo_url}

@router.get("/checklist")
async def get_onboarding_checklist(user_id: int):
    # Static checklist for now
    return [
        {"id": 1, "task": "Clone the repository", "completed": False, "xp": 50},
        {"id": 2, "task": "Install dependencies", "completed": False, "xp": 50},
        {"id": 3, "task": "Run the application", "completed": False, "xp": 50},
        {"id": 4, "task": "Fix the first bug (Login Issue)", "completed": False, "xp": 50},
        {"id": 5, "task": "Join the #general channel", "completed": False, "xp": 50},
        {"id": 6, "task": "Complete your first Standup", "completed": False, "xp": 50},
        {"id": 7, "task": "Submit a Pull Request", "completed": False, "xp": 50},
    ]
