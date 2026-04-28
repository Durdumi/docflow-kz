import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def migrate():
    from sqlalchemy import select, text
    from app.core.database import AsyncSessionLocal, engine
    from app.models.auth import Organization
    from app.models.tasks import Task

    async with AsyncSessionLocal() as db:
        orgs_result = await db.execute(select(Organization))
        orgs = orgs_result.scalars().all()

        for org in orgs:
            print(f"Processing {org.schema_name}...")
            await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))

            tasks_result = await db.execute(
                select(Task).where(Task.assignee_id.isnot(None))
            )
            tasks = tasks_result.scalars().all()

            count = 0
            for task in tasks:
                existing = [str(x) for x in (task.assignee_ids or [])]
                if str(task.assignee_id) not in existing:
                    task.assignee_ids = [str(task.assignee_id)] + existing
                    count += 1

            await db.commit()
            print(f"  Updated {count} tasks in {org.schema_name}")

        await db.execute(text("SET search_path TO public"))

    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(migrate())
