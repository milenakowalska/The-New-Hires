---
description: How to update the database schema using Alembic
---

# Update Database with Alembic

If you have modified `models.py`, you need to create a migration script to update the database schema.

## 1. Create a Migration Script

Run this command in the `backend` directory. Replace "description_of_change" with a brief description of what you changed (e.g., "add_user_role").

```bash
cd backend
alembic revision --autogenerate -m "description_of_change"
```

## 2. Apply the Migration

Once the revision script is created, apply it to the database:

```bash
cd backend
alembic upgrade head
```

## 3. Verify

Check if the changes were applied correctly. You can check the `alembic_version` table in your database or verify the schema changes.
