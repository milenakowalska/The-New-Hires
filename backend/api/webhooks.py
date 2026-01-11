from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
import hashlib
import hmac
import os
import httpx
from database import get_db
from models import User
from sqlalchemy.future import select
from .gamification_utils import update_effort_and_collaboration, update_quality
from .ai_utils import analyze_diff
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "your_webhook_secret")

async def verify_signature(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    body = await request.body()
    hash_object = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

async def process_pr_review(payload: dict, access_token: str):
    pull_request = payload.get("pull_request")
    owner = payload.get("repository", {}).get("owner", {}).get("login")
    repo = payload.get("repository", {}).get("name")
    pull_number = pull_request.get("number")
    diff_url = pull_request.get("diff_url")
    title = pull_request.get("title")

    if not access_token:
        print("No access token found for PR review")
        return

    # 1. Fetch Diff
    async with httpx.AsyncClient() as client:
        # We need to send headers to get the diff format, but diff_url is a public-ish redirect URL usually.
        # But for private repos or better reliability we use API.
        # Let's use the diff_url provided by webhook but add auth if needed.
        diff_res = await client.get(diff_url, headers={"Authorization": f"token {access_token}"}, follow_redirects=True)
        if diff_res.status_code != 200:
            print(f"Failed to fetch diff: {diff_res.status_code}")
            return
        diff_content = diff_res.text

    # 2. Analyze Code
    review_data = await analyze_diff(diff_content, title)
    comments = review_data.get("comments", [])
    
    if not comments:
        print("AI returned no comments.")
        return

    # 3. Post to GitHub
    # We can post a single "Review" with multiple comments
    review_body = {
        "body": "🤖 **Simulation AI Review**\n\nHere is my feedback on your code:",
        "event": "COMMENT", # or REQUEST_CHANGES
        "comments": []
    }
    
    # We need to map new file paths to the diff side
    # For simplicity in this demo, we assume "RIGHT" side.
    for comment in comments:
        # GitHub Review API structure
        review_body["comments"].append({
            "path": comment["file"],
            "line": int(comment["line"]),
            "body": f"💡 {comment['message']}"  
        })

    async with httpx.AsyncClient() as client:
        post_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        post_res = await client.post(
            post_url,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json=review_body
        )
        if post_res.status_code not in [200, 201]:
             print(f"Failed to post review: {post_res.text}")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    await verify_signature(request)
    
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    
    if event == "pull_request":
        action = payload.get("action")
        if action == "opened":
            # Find the user who owns this PR
            sender = payload.get("sender")
            if sender:
                github_id = str(sender.get("id"))
                stmt = select(User).where(User.github_id == github_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user and user.access_token:
                    # Run logic in background
                    background_tasks.add_task(process_pr_review, payload, user.access_token)
                    
                    from .activity import log_activity
                    from models import ActivityType
                    await log_activity(
                        db,
                        user.id,
                        ActivityType.PULL_REQUEST_OPENED,
                        f"Opened pull request: {payload.get('pull_request', {}).get('title')}",
                        {"pr_number": payload.get("pull_request", {}).get("number"), "repo": payload.get("repository", {}).get("name")}
                    )
        elif action == "closed":
            # Update ticket status?
            pass
            
    elif event == "workflow_run":
        action = payload.get("action")
        if action == "completed":
            workflow_run = payload.get("workflow_run", {})
            conclusion = workflow_run.get("conclusion")
            
            sender = payload.get("sender")
            if sender:
                github_id = str(sender.get("id"))
                stmt = select(User).where(User.github_id == github_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user and conclusion:
                    await update_quality(user, conclusion)
                    await db.commit()
            
    # Gamification Update
    sender = payload.get("sender")
    if sender:
        github_id = str(sender.get("id"))
        stmt = select(User).where(User.github_id == github_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            await update_effort_and_collaboration(user, event, payload)
            await db.commit()
            
    return {"status": "ok"}
