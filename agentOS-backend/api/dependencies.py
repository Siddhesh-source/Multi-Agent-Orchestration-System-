from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
