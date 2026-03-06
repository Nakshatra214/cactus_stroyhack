import os
import sys
from tasks.celery_app import celery_app
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@celery_app.task(bind=True, name="tasks.full_pipeline")
def task_full_pipeline(self, project_id: int):
    """One-stop background task for the entire generation pipeline."""
    from database.db import async_session
    from database.models import Project
    from sqlalchemy import select
    from services.script_service import generate_video_script
    from services.scene_service import create_scenes_from_script
    from services.video_service import (
        generate_all_visuals,
        generate_all_voices,
        build_all_scene_videos,
        build_final_video,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def run_pipeline():
            async with async_session() as db:
                # 1. Fetch project
                result = await db.execute(select(Project).where(Project.id == project_id))
                project = result.scalar_one_or_none()
                if not project:
                    return {"error": "Project not found"}
                
                # 2. Status: Processing Script
                project.status = "processing"
                await db.commit()
                
                print(f"[Pipeline] Generating script for project {project_id}")
                script_data = await generate_video_script(project.original_content)
                
                # Debug log
                with open("last_script_debug.json", "w") as f:
                    import json
                    json.dump(script_data, f)
                
                # 4. Create Scenes
                print(f"[Pipeline] Creating scenes for project {project_id}")
                await create_scenes_from_script(db, project_id, script_data)
                
                # 4. Status: Generating Visuals
                project.status = "visual_done" # We'll reuse these statuses for polling
                await db.commit()
                print(f"[Pipeline] Generating visuals for project {project_id}")
                await generate_all_visuals(db, project_id)
                
                # 5. Status: Generating Voice
                project.status = "voice_done"
                await db.commit()
                print(f"[Pipeline] Generating voices for project {project_id}")
                await generate_all_voices(db, project_id)
                
                # 6. Status: Building Video
                project.status = "building"
                await db.commit()
                print(f"[Pipeline] Building final video for project {project_id}")
                await build_all_scene_videos(db, project_id)
                final_url = await build_final_video(db, project_id)
                
                # 7. Final status
                project.status = "completed"
                await db.commit()
                
                print(f"[Pipeline] Completed! Final URL: {final_url}")
                return {"project_id": project_id, "final_video": final_url}
                
        return loop.run_until_complete(run_pipeline())
    except Exception as e:
        print(f"[Pipeline] ERROR: {str(e)}")
        return {"error": str(e)}
    finally:
        loop.close()
