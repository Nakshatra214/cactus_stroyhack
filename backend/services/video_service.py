"""
Video Service: Orchestrates visual + voice generation and video assembly.
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from agents.visual_agent import generate_visual
from agents.voice_agent import generate_voice
from video.scene_builder import build_scene_video
from video.video_merger import merge_scenes
from services.scene_service import get_scenes, get_scene
from database.models import Scene


async def generate_all_visuals(db: AsyncSession, project_id: int) -> List[dict]:
    """Generate visuals for all scenes in a project."""
    scenes = await get_scenes(db, project_id)
    results = []

    for scene in scenes:
        image_url = await generate_visual(
            prompt=scene.visual_prompt or f"Illustration for: {scene.scene_title}",
            scene_index=scene.scene_index,
            project_id=project_id,
        )
        scene.image_url = image_url
        scene.status = "visual_done"
        results.append({"scene_id": scene.id, "image_url": image_url})

    await db.commit()
    return results


async def generate_all_voices(db: AsyncSession, project_id: int) -> List[dict]:
    """Generate voiceover for all scenes in a project."""
    scenes = await get_scenes(db, project_id)
    results = []

    for scene in scenes:
        audio_url = await generate_voice(
            text=scene.script or scene.scene_title,
            scene_index=scene.scene_index,
            project_id=project_id,
            tone=scene.voice_tone,
        )
        scene.audio_url = audio_url
        scene.status = "voice_done"
        results.append({"scene_id": scene.id, "audio_url": audio_url})

    await db.commit()
    return results


async def build_all_scene_videos(db: AsyncSession, project_id: int) -> List[dict]:
    """Build individual video clips for each scene."""
    scenes = await get_scenes(db, project_id)
    results = []

    for scene in scenes:
        if scene.image_url and scene.audio_url:
            video_url = build_scene_video(
                image_path=scene.image_url,
                audio_path=scene.audio_url,
                scene_index=scene.scene_index,
                project_id=project_id,
                duration=scene.duration,
            )
            scene.video_clip = video_url
            scene.status = "completed"
            results.append({"scene_id": scene.id, "video_clip": video_url})

    await db.commit()
    return results


async def build_final_video(db: AsyncSession, project_id: int) -> str:
    """Merge all scene videos into the final video."""
    scenes = await get_scenes(db, project_id)
    scene_clips = [s.video_clip for s in scenes if s.video_clip]

    final_url = merge_scenes(scene_clips, project_id)

    # Update project
    from database.models import Project
    from sqlalchemy import select
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.final_video_url = final_url
        project.status = "completed"
        await db.commit()

    return final_url


async def regenerate_single_scene(db: AsyncSession, scene_id: int) -> dict:
    """Regenerate a single scene's visual, voice, and video without touching others."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return {"error": "Scene not found"}

    # Regenerate visual
    image_url = await generate_visual(
        prompt=scene.visual_prompt or f"Illustration for: {scene.scene_title}",
        scene_index=scene.scene_index,
        project_id=scene.project_id,
    )
    scene.image_url = image_url

    # Regenerate voice
    audio_url = await generate_voice(
        text=scene.script or scene.scene_title,
        scene_index=scene.scene_index,
        project_id=scene.project_id,
        tone=scene.voice_tone,
    )
    scene.audio_url = audio_url

    # Rebuild scene video
    video_url = build_scene_video(
        image_path=image_url,
        audio_path=audio_url,
        scene_index=scene.scene_index,
        project_id=scene.project_id,
        duration=scene.duration,
    )
    scene.video_clip = video_url
    scene.status = "completed"

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "image_url": image_url,
        "audio_url": audio_url,
        "video_clip": video_url,
    }
