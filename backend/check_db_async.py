import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import os
from models import User

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/thenewhire")

async def check():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()
        if user:
            print(f"User: {user.username}")
            print(f"Repo: {user.repo_full_name}")
            print(f"Last Indexed: {user.last_indexed_commit}")
        else:
            print("User 1 not found")
            
        # List all users with repos
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"ID: {u.id}, Name: {u.username}, Repo: {u.repo_full_name}")

if __name__ == "__main__":
    asyncio.run(check())
