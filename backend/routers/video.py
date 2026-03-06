"""
Video Router: Handles visual generation, voice generation, video building, and export.
"""
import asyncio
import os
import zipfile
import tempfile
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db, async_session
from database.models import Project, Scene
from services.planning_service import generate_video_plan_data, refine_scenes_with_storyboard
from services.scene_service import create_scenes_from_script
from services.video_service import (
    generate_all_visuals,
    generate_all_voices,
    build_all_scene_videos,
    build_final_video,
)

router = APIRouter()

class ProjectRequest(BaseModel):
    project_id: int


async def _run_pipeline_in_process(project_id: int) -> None:
    """Fallback background pipeline that does not depend on Celery workers."""
    async with async_session() as db:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return

        try:
            project.status = "processing"
            await db.commit()

            plan_data = await asyncio.wait_for(
                generate_video_plan_data(
                    content=project.original_content or "",
                    title=project.title or "Research Explainer",
                ),
                timeout=90,
            )
            await create_scenes_from_script(db, project_id, plan_data)
            await refine_scenes_with_storyboard(db, project_id)

            await generate_all_visuals(db, project_id)
            project.status = "visual_done"
            await db.commit()

            await generate_all_voices(db, project_id)
            project.status = "voice_done"
            await db.commit()

            await build_all_scene_videos(db, project_id)
            final_url = await build_final_video(db, project_id)
            project.final_video_url = final_url
            project.status = "completed"
            await db.commit()
        except Exception as e:
            print(f"[Pipeline] In-process pipeline failed for project {project_id}: {e}")
            project.status = "error"
            await db.commit()


@router.post("/process_video_async")
async def process_video_async(
    request: ProjectRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger full pipeline in background without requiring Celery availability."""
    result_task_id = f"local-{request.project_id}"
    background_tasks.add_task(_run_pipeline_in_process, request.project_id)
    return {"task_id": result_task_id, "project_id": request.project_id}

@router.post("/generate_visuals")
async def generate_visuals_endpoint(request: ProjectRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    results = await generate_all_visuals(db, request.project_id)
    return {"project_id": request.project_id, "visuals": results}

@router.post("/generate_voice")
async def generate_voice_endpoint(request: ProjectRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    results = await generate_all_voices(db, request.project_id)
    return {"project_id": request.project_id, "voices": results}

@router.post("/build_video")
async def build_video_endpoint(request: ProjectRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Build individual scene videos
    await build_all_scene_videos(db, request.project_id)
    # Merge into final
    final_url = await build_final_video(db, request.project_id)

    return {
        "project_id": request.project_id,
        "final_video": final_url,
    }

@router.get("/export_video/{project_id}")
async def export_video(project_id: int, format: str = "mp4", db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.final_video_url:
        raise HTTPException(status_code=404, detail="Video not found or not yet built")

    video_path = project.final_video_url[1:] if project.final_video_url.startswith("/storage/") else project.final_video_url
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    return FileResponse(
        path=video_path,
        media_type="video/mp4" if format == "mp4" else "image/gif",
        filename=f"{project.title or 'video'}_{project_id}.{format}",
    )

@router.get("/export_assets/{project_id}")
async def export_assets(project_id: int, db: AsyncSession = Depends(get_db)):
    """Export all scene images, audio, and scripts as a ZIP file."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project: raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_index))
    scenes = result.scalars().all()

    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, f"StoryHack_{project_id}_Assets.zip")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        script_text = f"# {project.title}\n\n"
        for s in scenes:
            scene_dir = f"Scene_{s.scene_index + 1}"
            script_text += f"## {s.scene_title}\n{s.script}\n\n"
            
            if s.image_url:
                p = s.image_url[1:] if s.image_url.startswith("/storage/") else s.image_url
                if os.path.exists(p): zipf.write(p, f"{scene_dir}/image.{p.split('.')[-1]}")
            if s.audio_url:
                p = s.audio_url[1:] if s.audio_url.startswith("/storage/") else s.audio_url
                if os.path.exists(p): zipf.write(p, f"{scene_dir}/audio.mp3")

        script_file = os.path.join(temp_dir, f"script_{project_id}.txt")
        with open(script_file, "w", encoding="utf-8") as f: f.write(script_text)
        zipf.write(script_file, "script.txt")

    return FileResponse(path=zip_path, media_type="application/zip", filename=f"StoryHack_{project_id}.zip")

@router.get("/project/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "final_video_url": project.final_video_url,
        "content_preview": (project.original_content or "")[:500],
    }
