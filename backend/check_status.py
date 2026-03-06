import asyncio
from database.db import async_session
from database.models import Project, Scene
from sqlalchemy import select

async def check():
    async with async_session() as db:
        res = await db.execute(select(Project).order_by(Project.id.desc()).limit(1))
        p = res.scalar_one_or_none()
        if p:
            print(f"LATEST PROJECT ID: {p.id}")
            print(f"Status: {p.status}")
            print(f"Title: {p.title}")
            print(f"Content Length: {len(p.original_content) if p.original_content else 0}")
            print(f"Final Video URL: {p.final_video_url}")
            
            scenes_res = await db.execute(select(Scene).where(Scene.project_id == p.id))
            scenes = scenes_res.scalars().all()
            print(f"Scenes Count for Project {p.id}: {len(scenes)}")
            for s in scenes:
                print(f" - Scene {s.scene_index}: Status={s.status}, Video={s.video_clip}")
            
            all_scenes_res = await db.execute(select(Scene))
            all_scenes = all_scenes_res.scalars().all()
            print(f"Total Scenes across all projects: {len(all_scenes)}")
        else:
            print("No projects found")

if __name__ == '__main__':
    asyncio.run(check())
