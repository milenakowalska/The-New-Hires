import pytest
from main import app
from database import AsyncSessionLocal
from models import User
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_onboarding_checklist_persistence():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a test user
        async with AsyncSessionLocal() as session:
            test_user = User(username="test_onboarding_user", xp=0)
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            user_id = test_user.id

        try:
            # 1. Get initial checklist
            response = await ac.get(f"/api/onboarding/checklist?user_id={user_id}")
            assert response.status_code == 200
            tasks = response.json()
            assert any(t["id"] == 1 and t["completed"] == False for t in tasks)

            # 2. Complete a task
            response = await ac.post(f"/api/onboarding/complete-task?user_id={user_id}", json={"task_id": 1})
            assert response.status_code == 200
            assert response.json()["xp_awarded"] == 50

            # 3. Verify persistence in checklist
            # We need to refresh the session or use a new one to see the updated user in the API if it's reused?
            # Actually AsyncClient call will get its own session via Depends(get_db)
            response = await ac.get(f"/api/onboarding/checklist?user_id={user_id}")
            assert response.status_code == 200
            tasks = response.json()
            assert any(t["id"] == 1 and t["completed"] == True for t in tasks)

            # 4. Attempt duplicate completion
            response = await ac.post(f"/api/onboarding/complete-task?user_id={user_id}", json={"task_id": 1})
            assert response.status_code == 200
            assert response.json()["xp_awarded"] == 0
        finally:
            # Cleanup
            async with AsyncSessionLocal() as session:
                from sqlalchemy import delete
                from models import Activity
                await session.execute(delete(Activity).where(Activity.user_id == user_id))
                await session.execute(delete(User).where(User.id == user_id))
                await session.commit()
