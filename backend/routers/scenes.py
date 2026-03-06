"""
Scenes Router: Handles scene CRUD, editing, regeneration, and versioning.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.models import Project
from services.scene_service import (
    create_scenes_from_script,
    get_scene,
    get_scene_versions,
    get_scenes,
    reorder_scenes,
    revert_scene,
    scene_to_dict,
    scene_version_to_dict,
    update_scene,
)
from services.video_service import regenerate_single_scene

router = APIRouter()


class GenerateScenesRequest(BaseModel):
    project_id: int
    script: dict  # Supports {scenes:[...]} or {video_plan:{scenes:[...]}}


class EditSceneRequest(BaseModel):
    scene_id: int
    script: Optional[str] = None
    visual_prompt: Optional[str] = None
    visual_description: Optional[str] = None
    camera_shot: Optional[str] = None
    animation_type: Optional[str] = None
    motion_direction: Optional[str] = None
    visual_layers: Optional[List[str]] = None
    text_overlay: Optional[str] = None
    transition: Optional[str] = None
    voice_tone: Optional[str] = None
    duration: Optional[float] = None
    scene_title: Optional[str] = None
    source_reference: Optional[str] = None
    confidence_score: Optional[float] = None


class RegenerateSceneRequest(BaseModel):
    scene_id: int


class ReorderScenesRequest(BaseModel):
    project_id: int
    scene_order: List[int]


class RevertSceneRequest(BaseModel):
    scene_id: int
    version: int


@router.post("/generate_scenes")
async def generate_scenes_endpoint(request: GenerateScenesRequest, db: AsyncSession = Depends(get_db)):
    """Create scene records from generated script data."""
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = await create_scenes_from_script(db, request.project_id, request.script)
    return {
        "project_id": request.project_id,
        "scene_count": len(scenes),
        "scenes": [scene_to_dict(s) for s in scenes],
    }


@router.get("/scenes/{project_id}")
async def get_project_scenes(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get all scenes for a project."""
    scenes = await get_scenes(db, project_id)
    return {
        "project_id": project_id,
        "scene_count": len(scenes),
        "scenes": [scene_to_dict(s) for s in scenes],
    }


@router.post("/edit_scene")
async def edit_scene_endpoint(request: EditSceneRequest, db: AsyncSession = Depends(get_db)):
    """Edit a scene's planning/script/animation properties."""
    updates = request.model_dump(exclude_none=True) if hasattr(request, "model_dump") else request.dict(exclude_none=True)
    updates.pop("scene_id", None)

    scene = await update_scene(db, request.scene_id, updates)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    return scene_to_dict(scene)


class AgenticEditSceneRequest(BaseModel):
    scene_id: int
    user_instruction: str


@router.post("/agentic_edit_scene")
async def agentic_edit_scene_endpoint(request: AgenticEditSceneRequest, db: AsyncSession = Depends(get_db)):
    """Use AI to intelligently edit a scene based on a user instruction."""
    scene = await get_scene(db, request.scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    current_scene_dict = {
        "title": scene.scene_title,
        "narration_script": scene.script,
        "visual_description": scene.visual_description,
        "visual_prompt": scene.visual_prompt,
        "camera_shot": scene.camera_shot,
        "animation_type": scene.animation_type,
        "motion_direction": scene.motion_direction,
        "visual_layers": scene_to_dict(scene).get("visual_layers", []),
        "text_overlay": scene.text_overlay,
        "transition": scene.transition,
        "voice_tone": scene.voice_tone,
        "duration": scene.duration,
    }

    import json
    from agents.edit_agent import agentic_edit_scene

    updated_scene = await agentic_edit_scene(
        current_scene_json=json.dumps(current_scene_dict),
        user_instruction=request.user_instruction,
    )

    updates = {}
    if "title" in updated_scene:
        updates["scene_title"] = updated_scene["title"]
    if "narration_script" in updated_scene:
        updates["script"] = updated_scene["narration_script"]
    if "visual_prompt" in updated_scene:
        updates["visual_prompt"] = updated_scene["visual_prompt"]
    if "visual_description" in updated_scene:
        updates["visual_description"] = updated_scene["visual_description"]
    if "camera_shot" in updated_scene:
        updates["camera_shot"] = updated_scene["camera_shot"]
    if "animation_type" in updated_scene:
        updates["animation_type"] = updated_scene["animation_type"]
    if "motion_direction" in updated_scene:
        updates["motion_direction"] = updated_scene["motion_direction"]
    if "visual_layers" in updated_scene:
        updates["visual_layers"] = updated_scene["visual_layers"]
    if "text_overlay" in updated_scene:
        updates["text_overlay"] = updated_scene["text_overlay"]
    if "transition" in updated_scene:
        updates["transition"] = updated_scene["transition"]
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

    return scene_to_dict(updated_scene_db)


@router.post("/regenerate_scene")
async def regenerate_scene_endpoint(request: RegenerateSceneRequest, db: AsyncSession = Depends(get_db)):
    """Regenerate a single scene (visual + voice + video) without touching others."""
    result = await regenerate_single_scene(db, request.scene_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/scene_versions/{scene_id}")
async def get_scene_versions_endpoint(scene_id: int, db: AsyncSession = Depends(get_db)):
    """Get version history for a scene."""
    versions = await get_scene_versions(db, scene_id)
    return {
        "scene_id": scene_id,
        "versions": [scene_version_to_dict(v) for v in versions],
    }


@router.post("/revert_scene")
async def revert_scene_endpoint(request: RevertSceneRequest, db: AsyncSession = Depends(get_db)):
    """Revert a scene to a previous version."""
    scene = await revert_scene(db, request.scene_id, request.version)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene or version not found")
    return scene_to_dict(scene)


@router.post("/reorder_scenes")
async def reorder_scenes_endpoint(request: ReorderScenesRequest, db: AsyncSession = Depends(get_db)):
    """Reorder scenes via drag-and-drop."""
    scenes = await reorder_scenes(db, request.project_id, request.scene_order)
    return {
        "project_id": request.project_id,
        "scenes": [
            {"id": s.id, "scene_index": s.scene_index, "scene_title": s.scene_title}
            for s in scenes
        ],
    }
