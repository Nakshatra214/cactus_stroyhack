"""
Celery tasks for long-running operations.
These provide async task execution for video generation pipeline steps.
"""
from tasks.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.generate_script")
def task_generate_script(self, project_id: int, content: str):
    """Background task for script generation."""
    import asyncio
    from services.script_service import generate_video_script

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(generate_video_script(content))
        return {"project_id": project_id, "script": result}
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.generate_visuals")
def task_generate_visuals(self, project_id: int):
    """Background task for generating all scene visuals."""
    import asyncio
    from database.db import async_session
    from services.video_service import generate_all_visuals

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def run():
            async with async_session() as db:
                return await generate_all_visuals(db, project_id)
        result = loop.run_until_complete(run())
        return {"project_id": project_id, "visuals": [r for r in result]}
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.build_video")
def task_build_video(self, project_id: int):
    """Background task for building the final video."""
    import asyncio
    from database.db import async_session
    from services.video_service import build_all_scene_videos, build_final_video

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def run():
            async with async_session() as db:
                await build_all_scene_videos(db, project_id)
                return await build_final_video(db, project_id)
        result = loop.run_until_complete(run())
        return {"project_id": project_id, "final_video": result}
    finally:
        loop.close()
