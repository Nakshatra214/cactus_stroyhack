"""
Script Router: Handles script generation from uploaded content.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Project
from services.planning_service import generate_video_plan_data
from services.script_service import generate_video_script

router = APIRouter()


class GenerateScriptRequest(BaseModel):
    project_id: int


class GenerateVideoPlanRequest(BaseModel):
    project_id: int


@router.post("/generate_script")
async def generate_script(
    request: GenerateScriptRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a video script from project content."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.original_content:
        raise HTTPException(status_code=400, detail="Project has no content")

    # Generate script
    script_data = await generate_video_script(project.original_content)

    # Update project status
    project.status = "scripted"
    await db.commit()

    return {
        "project_id": project.id,
        "script": script_data,
        "scene_count": len(script_data.get("scenes", [])),
    }


@router.post("/generate_video_plan")
async def generate_video_plan(
    request: GenerateVideoPlanRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a strict video_plan JSON from project content."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.original_content:
        raise HTTPException(status_code=400, detail="Project has no content")

    plan = await generate_video_plan_data(
        content=project.original_content,
        title=project.title,
    )
    return {"video_plan": plan.get("video_plan", {})}
