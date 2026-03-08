import asyncio
from db.database import AsyncSessionLocal
from db.models import Task
from sqlalchemy import select

async def check_recent():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Task).order_by(Task.created_at.desc()).limit(5)
        )
        tasks = result.scalars().all()
        print(f'Total recent tasks: {len(tasks)}\n')
        for task in tasks:
            print(f'Task ID: {task.id}')
            print(f'Description: {task.description[:60]}...')
            print(f'Status: {task.status}')
            print(f'Created: {task.created_at}')
            print(f'---')

asyncio.run(check_recent())
