"""
Video Router: Handles visual generation, voice generation, video building, and export.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Project
from services.video_service import (
    generate_all_visuals,
    generate_all_voices,
    build_all_scene_videos,
    build_final_video,
)

router = APIRouter()


class ProjectRequest(BaseModel):
    project_id: int


@router.post("/generate_visuals")
async def generate_visuals_endpoint(
    request: ProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate visuals for all scenes in a project."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = await generate_all_visuals(db, request.project_id)
    return {"project_id": request.project_id, "visuals": results}


@router.post("/generate_voice")
async def generate_voice_endpoint(
    request: ProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate voiceover for all scenes in a project."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = await generate_all_voices(db, request.project_id)
    return {"project_id": request.project_id, "voices": results}


@router.post("/build_video")
async def build_video_endpoint(
    request: ProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Build scene videos and merge into final video."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build individual scene videos
    scene_results = await build_all_scene_videos(db, request.project_id)

    # Merge into final
    final_url = await build_final_video(db, request.project_id)

    return {
        "project_id": request.project_id,
        "scene_videos": scene_results,
        "final_video": final_url,
    }


@router.get("/export_video/{project_id}")
async def export_video(
    project_id: int,
    format: str = "mp4",
    db: AsyncSession = Depends(get_db),
):
    """Export the final video for download."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.final_video_url:
        raise HTTPException(status_code=400, detail="No final video available. Build the video first.")

    # Resolve file path
    video_path = project.final_video_url
    if video_path.startswith("/storage/"):
        video_path = video_path[1:]

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    media_type = "video/mp4"
    if format == "gif":
        media_type = "image/gif"

    return FileResponse(
        path=video_path,
        media_type=media_type,
        filename=f"{project.title}_{project_id}.{format}",
    )


@router.get("/project/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "final_video_url": project.final_video_url,
        "created_at": str(project.created_at),
        "content_preview": (project.original_content or "")[:500],
    }
