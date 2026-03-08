"""
Scene Service: CRUD operations and version management for scenes.
"""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Scene, SceneVersion


def _serialize_visual_layers(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps([str(v).strip() for v in value if str(v).strip()])
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return "[]"
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps([str(v).strip() for v in parsed if str(v).strip()])
        except Exception:
            pass
        return json.dumps([v.strip() for v in value.split(",") if v.strip()])
    return "[]"


def _deserialize_visual_layers(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
        return [seg.strip() for seg in text.split(",") if seg.strip()]
    return []


def _clamp_confidence(value: Any) -> float:
    try:
        score = float(value)
    except Exception:
        score = 0.8
    return max(0.0, min(1.0, round(score, 2)))


def scene_to_dict(scene: Scene) -> Dict[str, Any]:
    return {
        "id": scene.id,
        "scene_index": scene.scene_index,
        "scene_title": scene.scene_title,
        "script": scene.script,
        "visual_prompt": scene.visual_prompt,
        "visual_description": scene.visual_description,
        "camera_shot": scene.camera_shot,
        "animation_type": scene.animation_type,
        "motion_direction": scene.motion_direction,
        "visual_layers": _deserialize_visual_layers(scene.visual_layers),
        "text_overlay": scene.text_overlay,
        "transition": scene.transition,
        "image_url": scene.image_url,
        "audio_url": scene.audio_url,
        "video_clip": scene.video_clip,
        "source_reference": scene.source_reference,
        "confidence_score": scene.confidence_score,
        "version": scene.version,
        "duration": scene.duration,
        "voice_tone": scene.voice_tone,
        "status": scene.status,
    }


def scene_version_to_dict(version: SceneVersion) -> Dict[str, Any]:
    return {
        "version": version.version,
        "script": version.script,
        "visual_prompt": version.visual_prompt,
        "visual_description": version.visual_description,
        "camera_shot": version.camera_shot,
        "animation_type": version.animation_type,
        "motion_direction": version.motion_direction,
        "visual_layers": _deserialize_visual_layers(version.visual_layers),
        "text_overlay": version.text_overlay,
        "transition": version.transition,
        "image_url": version.image_url,
        "audio_url": version.audio_url,
        "video_clip": version.video_clip,
        "confidence_score": version.confidence_score,
        "source_reference": version.source_reference,
        "created_at": str(version.created_at),
    }


def _extract_scene_list(script_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "video_plan" in script_data and isinstance(script_data["video_plan"], dict):
        scenes = script_data["video_plan"].get("scenes", [])
        if isinstance(scenes, list):
            return scenes
    scenes = script_data.get("scenes", [])
    if isinstance(scenes, list):
        return scenes
    return []


async def create_scenes_from_script(db: AsyncSession, project_id: int, script_data: dict) -> List[Scene]:
    """
    Create scene records from generated script/video-plan data.
    Supports both {scenes:[...]} and {video_plan:{scenes:[...]}} shapes.
    """
    scenes = []
    scene_list = _extract_scene_list(script_data)

    for i, scene_data in enumerate(scene_list):
        if not isinstance(scene_data, dict):
            scene_data = {}

        scene = Scene(
            project_id=project_id,
            scene_index=i,
            scene_title=scene_data.get("title", f"Scene {i + 1}"),
            script=scene_data.get("narration_script", scene_data.get("narration", "")),
            visual_prompt=scene_data.get("visual_prompt", ""),
            visual_description=scene_data.get("visual_description", ""),
            camera_shot=scene_data.get("camera_shot", "medium shot"),
            animation_type=scene_data.get("animation_type", "zoom"),
            motion_direction=scene_data.get("motion_direction", "slow zoom in"),
            visual_layers=_serialize_visual_layers(scene_data.get("visual_layers", [])),
            text_overlay=scene_data.get("text_overlay", scene_data.get("title", f"Scene {i + 1}")),
            transition=scene_data.get("transition", "fade"),
            source_reference=scene_data.get("source_reference", ""),
            confidence_score=_clamp_confidence(scene_data.get("confidence_score", scene_data.get("confidence", 0.8))),
            voice_tone=scene_data.get("voice_tone", "neutral"),
            duration=scene_data.get("duration", 6.0),
            version=1,
            status="pending",
        )
        db.add(scene)
        scenes.append(scene)

    await db.commit()
    for s in scenes:
        await db.refresh(s)

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.status = "scripted"
        await db.commit()

    return scenes


async def get_scenes(db: AsyncSession, project_id: int) -> List[Scene]:
    """Get all scenes for a project, ordered by scene_index."""
    result = await db.execute(select(Scene).where(Scene.project_id == project_id).order_by(Scene.scene_index))
    return list(result.scalars().all())


async def get_scene(db: AsyncSession, scene_id: int) -> Optional[Scene]:
    """Get a single scene by ID."""
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    return result.scalar_one_or_none()


async def _create_scene_version(db: AsyncSession, scene: Scene) -> None:
    version_record = SceneVersion(
        scene_id=scene.id,
        version=scene.version,
        script=scene.script,
        visual_prompt=scene.visual_prompt,
        visual_description=scene.visual_description,
        camera_shot=scene.camera_shot,
        animation_type=scene.animation_type,
        motion_direction=scene.motion_direction,
        visual_layers=scene.visual_layers,
        text_overlay=scene.text_overlay,
        transition=scene.transition,
        image_url=scene.image_url,
        audio_url=scene.audio_url,
        video_clip=scene.video_clip,
        source_reference=scene.source_reference,
        confidence_score=scene.confidence_score,
    )
    db.add(version_record)


async def update_scene(db: AsyncSession, scene_id: int, updates: dict) -> Optional[Scene]:
    """Update a scene and save the previous version."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return None

    await _create_scene_version(db, scene)

    simple_fields = [
        "script",
        "visual_prompt",
        "visual_description",
        "camera_shot",
        "animation_type",
        "motion_direction",
        "text_overlay",
        "transition",
        "voice_tone",
        "duration",
        "scene_title",
        "scene_index",
        "source_reference",
    ]
    for field in simple_fields:
        if field in updates:
            setattr(scene, field, updates[field])

    if "confidence_score" in updates:
        scene.confidence_score = _clamp_confidence(updates["confidence_score"])
    if "visual_layers" in updates:
        scene.visual_layers = _serialize_visual_layers(updates["visual_layers"])

    update_fields = set(updates.keys())
    narration_changed = bool(update_fields & {"script", "voice_tone", "duration"})
    visuals_changed = bool(update_fields & {"visual_prompt", "visual_description"})
    animation_changed = bool(update_fields & {"animation_type", "motion_direction", "transition", "text_overlay", "visual_layers"})

    if visuals_changed:
        scene.image_url = None
    if narration_changed:
        scene.audio_url = None
    if visuals_changed or narration_changed or animation_changed:
        scene.video_clip = None

    scene.version += 1
    scene.status = "pending"

    await db.commit()
    await db.refresh(scene)
    return scene


async def get_scene_versions(db: AsyncSession, scene_id: int) -> List[SceneVersion]:
    """Get all versions of a scene."""
    result = await db.execute(select(SceneVersion).where(SceneVersion.scene_id == scene_id).order_by(SceneVersion.version.desc()))
    return list(result.scalars().all())


async def revert_scene(db: AsyncSession, scene_id: int, version: int) -> Optional[Scene]:
    """Revert a scene to a previous version."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return None

    result = await db.execute(select(SceneVersion).where(SceneVersion.scene_id == scene_id, SceneVersion.version == version))
    version_record = result.scalar_one_or_none()
    if not version_record:
        return None

    await _create_scene_version(db, scene)

    scene.script = version_record.script
    scene.visual_prompt = version_record.visual_prompt
    scene.visual_description = version_record.visual_description
    scene.camera_shot = version_record.camera_shot
    scene.animation_type = version_record.animation_type
    scene.motion_direction = version_record.motion_direction
    scene.visual_layers = version_record.visual_layers
    scene.text_overlay = version_record.text_overlay
    scene.transition = version_record.transition
    scene.image_url = version_record.image_url
    scene.audio_url = version_record.audio_url
    scene.video_clip = version_record.video_clip
    scene.source_reference = version_record.source_reference
    scene.confidence_score = version_record.confidence_score
    scene.version += 1
    scene.status = "pending"

    await db.commit()
    await db.refresh(scene)
    return scene


async def reorder_scenes(db: AsyncSession, project_id: int, scene_order: List[int]) -> List[Scene]:
    """Reorder scenes by updating their scene_index."""
    scenes = await get_scenes(db, project_id)
    scene_map = {s.id: s for s in scenes}

    for new_index, scene_id in enumerate(scene_order):
        if scene_id in scene_map:
            scene_map[scene_id].scene_index = new_index

    await db.commit()
    return await get_scenes(db, project_id)
