"""
Scene Service: CRUD operations and version management for scenes.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Scene, SceneVersion, Project


async def create_scenes_from_script(db: AsyncSession, project_id: int,
                                     script_data: dict) -> List[Scene]:
    """Create scene records from generated script data."""
    scenes = []
    for i, scene_data in enumerate(script_data.get("scenes", [])):
        scene = Scene(
            project_id=project_id,
            scene_index=i,
            scene_title=scene_data.get("title", f"Scene {i + 1}"),
            script=scene_data.get("narration_script", scene_data.get("narration", "")),
            visual_prompt=scene_data.get("visual_prompt", ""),
            source_reference=scene_data.get("source_reference", ""),
            confidence_score=scene_data.get("confidence_score", scene_data.get("confidence", 0.8)),
            voice_tone=scene_data.get("voice_tone", "neutral"),
            duration=scene_data.get("duration", 5.0),
            version=1,
            status="pending",
        )
        db.add(scene)
        scenes.append(scene)

    await db.commit()
    for s in scenes:
        await db.refresh(s)

    # Update project status
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.status = "scripted"
        await db.commit()

    return scenes


async def get_scenes(db: AsyncSession, project_id: int) -> List[Scene]:
    """Get all scenes for a project, ordered by scene_index."""
    result = await db.execute(
        select(Scene)
        .where(Scene.project_id == project_id)
        .order_by(Scene.scene_index)
    )
    return list(result.scalars().all())


async def get_scene(db: AsyncSession, scene_id: int) -> Optional[Scene]:
    """Get a single scene by ID."""
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    return result.scalar_one_or_none()


async def update_scene(db: AsyncSession, scene_id: int, updates: dict) -> Optional[Scene]:
    """Update a scene and save the previous version."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return None

    # Save current version to history
    version_record = SceneVersion(
        scene_id=scene.id,
        version=scene.version,
        script=scene.script,
        visual_prompt=scene.visual_prompt,
        image_url=scene.image_url,
        audio_url=scene.audio_url,
        video_clip=scene.video_clip,
        source_reference=scene.source_reference,
        confidence_score=scene.confidence_score,
    )
    db.add(version_record)

    # Apply updates
    if "script" in updates:
        scene.script = updates["script"]
    if "visual_prompt" in updates:
        scene.visual_prompt = updates["visual_prompt"]
    if "voice_tone" in updates:
        scene.voice_tone = updates["voice_tone"]
    if "duration" in updates:
        scene.duration = updates["duration"]
    if "scene_title" in updates:
        scene.scene_title = updates["scene_title"]
    if "scene_index" in updates:
        scene.scene_index = updates["scene_index"]

    scene.version += 1
    scene.status = "pending"

    await db.commit()
    await db.refresh(scene)
    return scene


async def get_scene_versions(db: AsyncSession, scene_id: int) -> List[SceneVersion]:
    """Get all versions of a scene."""
    result = await db.execute(
        select(SceneVersion)
        .where(SceneVersion.scene_id == scene_id)
        .order_by(SceneVersion.version.desc())
    )
    return list(result.scalars().all())


async def revert_scene(db: AsyncSession, scene_id: int, version: int) -> Optional[Scene]:
    """Revert a scene to a previous version."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return None

    result = await db.execute(
        select(SceneVersion)
        .where(SceneVersion.scene_id == scene_id, SceneVersion.version == version)
    )
    version_record = result.scalar_one_or_none()
    if not version_record:
        return None

    # Save current as new version first
    current_version = SceneVersion(
        scene_id=scene.id,
        version=scene.version,
        script=scene.script,
        visual_prompt=scene.visual_prompt,
        image_url=scene.image_url,
        audio_url=scene.audio_url,
        video_clip=scene.video_clip,
        source_reference=scene.source_reference,
        confidence_score=scene.confidence_score,
    )
    db.add(current_version)

    # Revert to target version
    scene.script = version_record.script
    scene.visual_prompt = version_record.visual_prompt
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


async def reorder_scenes(db: AsyncSession, project_id: int,
                          scene_order: List[int]) -> List[Scene]:
    """Reorder scenes by updating their scene_index."""
    scenes = await get_scenes(db, project_id)
    scene_map = {s.id: s for s in scenes}

    for new_index, scene_id in enumerate(scene_order):
        if scene_id in scene_map:
            scene_map[scene_id].scene_index = new_index

    await db.commit()
    return await get_scenes(db, project_id)
