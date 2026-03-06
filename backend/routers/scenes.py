"""
Scenes Router: Handles scene CRUD, editing, regeneration, and versioning.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.scene_service import (
    create_scenes_from_script,
    get_scenes,
    get_scene,
    update_scene,
    get_scene_versions,
    revert_scene,
    reorder_scenes,
)
from services.video_service import regenerate_single_scene, build_final_video
from services.script_service import generate_video_script
from database.models import Project
from sqlalchemy import select

router = APIRouter()


class GenerateScenesRequest(BaseModel):
    project_id: int
    script: dict  # The script data from /generate_script


class EditSceneRequest(BaseModel):
    scene_id: int
    script: Optional[str] = None
    visual_prompt: Optional[str] = None
    voice_tone: Optional[str] = None
    duration: Optional[float] = None
    scene_title: Optional[str] = None


class RegenerateSceneRequest(BaseModel):
    scene_id: int


class ReorderScenesRequest(BaseModel):
    project_id: int
    scene_order: List[int]  # List of scene IDs in new order


class RevertSceneRequest(BaseModel):
    scene_id: int
    version: int


@router.post("/generate_scenes")
async def generate_scenes_endpoint(
    request: GenerateScenesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create scene records from a generated script."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = await create_scenes_from_script(db, request.project_id, request.script)

    return {
        "project_id": request.project_id,
        "scene_count": len(scenes),
        "scenes": [
            {
                "id": s.id,
                "scene_index": s.scene_index,
                "scene_title": s.scene_title,
                "script": s.script,
                "visual_prompt": s.visual_prompt,
                "source_reference": s.source_reference,
                "confidence_score": s.confidence_score,
                "version": s.version,
                "status": s.status,
            }
            for s in scenes
        ],
    }


@router.get("/scenes/{project_id}")
async def get_project_scenes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all scenes for a project."""
    scenes = await get_scenes(db, project_id)
    return {
        "project_id": project_id,
        "scene_count": len(scenes),
        "scenes": [
            {
                "id": s.id,
                "scene_index": s.scene_index,
                "scene_title": s.scene_title,
                "script": s.script,
                "visual_prompt": s.visual_prompt,
                "image_url": s.image_url,
                "audio_url": s.audio_url,
                "video_clip": s.video_clip,
                "source_reference": s.source_reference,
                "confidence_score": s.confidence_score,
                "version": s.version,
                "duration": s.duration,
                "voice_tone": s.voice_tone,
                "status": s.status,
            }
            for s in scenes
        ],
    }


@router.post("/edit_scene")
async def edit_scene_endpoint(
    request: EditSceneRequest,
    db: AsyncSession = Depends(get_db),
):
    """Edit a scene's script, visual prompt, or other properties."""
    updates = {}
    if request.script is not None:
        updates["script"] = request.script
    if request.visual_prompt is not None:
        updates["visual_prompt"] = request.visual_prompt
    if request.voice_tone is not None:
        updates["voice_tone"] = request.voice_tone
    if request.duration is not None:
        updates["duration"] = request.duration
    if request.scene_title is not None:
        updates["scene_title"] = request.scene_title

    scene = await update_scene(db, request.scene_id, updates)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    return {
        "id": scene.id,
        "scene_title": scene.scene_title,
        "script": scene.script,
        "visual_prompt": scene.visual_prompt,
        "version": scene.version,
        "status": scene.status,
    }


class AgenticEditSceneRequest(BaseModel):
    scene_id: int
    user_instruction: str

@router.post("/agentic_edit_scene")
async def agentic_edit_scene_endpoint(
    request: AgenticEditSceneRequest,
    db: AsyncSession = Depends(get_db),
):
    """Use AI to intelligently edit a scene based on a user instruction."""
    scene = await get_scene(db, request.scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Construct the JSON representation of the current scene
    current_scene_dict = {
        "title": scene.scene_title,
        "narration_script": scene.script,
        "visual_prompt": scene.visual_prompt,
        "voice_tone": scene.voice_tone,
        "duration": scene.duration,
    }

    import json
    from agents.edit_agent import agentic_edit_scene

    # Call the LLM to get the updated JSON
    updated_scene = await agentic_edit_scene(
        current_scene_json=json.dumps(current_scene_dict),
        user_instruction=request.user_instruction,
    )

    # Prepare updates mapping the returned JSON keys back to the DB columns
    updates = {}
    if "title" in updated_scene:
        updates["scene_title"] = updated_scene["title"]
    if "narration_script" in updated_scene:
        updates["script"] = updated_scene["narration_script"]
    if "visual_prompt" in updated_scene:
        updates["visual_prompt"] = updated_scene["visual_prompt"]
    if "voice_tone" in updated_scene:
        updates["voice_tone"] = updated_scene["voice_tone"]
    if "duration" in updated_scene:
        try:
            updates["duration"] = float(updated_scene["duration"])
        except (ValueError, TypeError):
            pass

    updated_scene_db = await update_scene(db, request.scene_id, updates)
    if not updated_scene_db:
        raise HTTPException(status_code=500, detail="Failed to update scene after AI edit")

    return {
        "id": updated_scene_db.id,
        "scene_title": updated_scene_db.scene_title,
        "script": updated_scene_db.script,
        "visual_prompt": updated_scene_db.visual_prompt,
        "voice_tone": updated_scene_db.voice_tone,
        "duration": updated_scene_db.duration,
        "version": updated_scene_db.version,
        "status": updated_scene_db.status,
    }


@router.post("/regenerate_scene")
async def regenerate_scene_endpoint(
    request: RegenerateSceneRequest,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a single scene (visual + voice + video) without touching others."""
    result = await regenerate_single_scene(db, request.scene_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/scene_versions/{scene_id}")
async def get_scene_versions_endpoint(
    scene_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get version history for a scene."""
    versions = await get_scene_versions(db, scene_id)
    return {
        "scene_id": scene_id,
        "versions": [
            {
                "version": v.version,
                "script": v.script,
                "visual_prompt": v.visual_prompt,
                "image_url": v.image_url,
                "confidence_score": v.confidence_score,
                "created_at": str(v.created_at),
            }
            for v in versions
        ],
    }


@router.post("/revert_scene")
async def revert_scene_endpoint(
    request: RevertSceneRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revert a scene to a previous version."""
    scene = await revert_scene(db, request.scene_id, request.version)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene or version not found")
    return {
        "id": scene.id,
        "version": scene.version,
        "script": scene.script,
        "visual_prompt": scene.visual_prompt,
        "status": scene.status,
    }


@router.post("/reorder_scenes")
async def reorder_scenes_endpoint(
    request: ReorderScenesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reorder scenes via drag-and-drop."""
    scenes = await reorder_scenes(db, request.project_id, request.scene_order)
    return {
        "project_id": request.project_id,
        "scenes": [{"id": s.id, "scene_index": s.scene_index, "scene_title": s.scene_title} for s in scenes],
    }
