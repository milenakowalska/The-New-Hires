from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import os
from models import User

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/thenewhire")
# convert async url to sync for simplicity in check script
SYNC_DATABASE_URL = DATABASE_URL.replace("asyncpg", "psycopg2")

engine = create_engine(SYNC_DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter(User.id == 1).first()
if user:
    print(f"User: {user.username}")
    print(f"Repo: {user.repo_full_name}")
    print(f"Last Indexed: {user.last_indexed_commit}")
else:
    print("User 1 not found")

# Check all users
all_users = session.query(User).all()
print(f"Total users: {len(all_users)}")
for u in all_users:
    print(f"ID: {u.id}, Name: {u.username}, Repo: {u.repo_full_name}")
