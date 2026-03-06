"""
Video Router: Handles visual generation, voice generation, video building, and export.
"""
import os
import zipfile
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Project, Scene
from services.video_service import (
    generate_all_visuals,
    generate_all_voices,
    build_all_scene_videos,
    build_final_video,
)

router = APIRouter()

class ProjectRequest(BaseModel):
    project_id: int


@router.post("/process_video_async")
async def process_video_async(
    request: ProjectRequest,
):
    """Trigger the full generation pipeline in the background."""
    from tasks.tasks import task_full_pipeline
    task = task_full_pipeline.delay(request.project_id)
    return {"task_id": task.id, "project_id": request.project_id}

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
