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
    from services.scene_service import create_scenes_from_script
    from services.planning_service import generate_video_plan_data, refine_scenes_with_storyboard
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
                
                print(f"[Pipeline] Generating video plan for project {project_id}")
                plan_data = await generate_video_plan_data(
                    content=project.original_content or "",
                    title=project.title or "Research Explainer",
                )
                
                # Debug log
                with open("last_video_plan_debug.json", "w", encoding="utf-8") as f:
                    import json
                    json.dump(plan_data, f, ensure_ascii=False, indent=2)
                
                # 3. Create scenes from plan
                print(f"[Pipeline] Creating scenes for project {project_id}")
                await create_scenes_from_script(db, project_id, plan_data)

                # 4. Optional storyboard refinement
                print(f"[Pipeline] Refining storyboard for project {project_id}")
                await refine_scenes_with_storyboard(db, project_id)
                
                # 5. Generate visuals
                print(f"[Pipeline] Generating visuals for project {project_id}")
                await generate_all_visuals(db, project_id)
                project.status = "visual_done"
                await db.commit()
                
                # 6. Generate voice
                print(f"[Pipeline] Generating voices for project {project_id}")
                await generate_all_voices(db, project_id)
                project.status = "voice_done"
                await db.commit()
                
                # 7. Build and merge video
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
