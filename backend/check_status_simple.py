import asyncio
from database.db import async_session
from database.models import Project
from sqlalchemy import select

async def check():
    async with async_session() as db:
        res = await db.execute(select(Project).order_by(Project.id.desc()).limit(5))
        projects = res.scalars().all()
        for p in projects:
            print(f"ID: {p.id}, Status: {p.status}, Title: {p.title}")

if __name__ == '__main__':
    asyncio.run(check())
