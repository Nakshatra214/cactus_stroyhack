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


async def generate_all_visuals(db: AsyncSession, project_id: int) -> List[dict]:
    """Generate visuals for all scenes in a project."""
    scenes = await get_scenes(db, project_id)
    results = []

    for scene in scenes:
        visual_data = await generate_visual(
            prompt=scene.visual_prompt or f"Illustration for: {scene.scene_title}",
            scene_index=scene.scene_index,
            project_id=project_id,
        )
        if isinstance(visual_data, dict):
            scene.image_url = visual_data.get("image_url")
            if not scene.animation_type and visual_data.get("animation_type"):
                scene.animation_type = visual_data.get("animation_type")
            if not scene.motion_direction and visual_data.get("motion_direction"):
                scene.motion_direction = visual_data.get("motion_direction")
        else:
            scene.image_url = visual_data
            
        scene.status = "visual_done"
        results.append({"scene_id": scene.id, "image_url": scene.image_url})

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
            video_url = await build_scene_video(
                image_path=scene.image_url,
                audio_path=scene.audio_url,
                scene_index=scene.scene_index,
                project_id=project_id,
                duration=scene.duration,
                animation_type=scene.animation_type or "zoom",
                motion_direction=scene.motion_direction or "",
            )
            scene.video_clip = video_url if video_url else None
            scene.status = "completed"  # Mark completed even without video — image+audio exist
            results.append({"scene_id": scene.id, "video_clip": video_url or None})

    await db.commit()
    return results


async def build_final_video(db: AsyncSession, project_id: int) -> str:
    """Merge all scene videos into the final video."""
    scenes = await get_scenes(db, project_id)
    scene_clips = [s.video_clip for s in scenes if s.video_clip and s.video_clip.strip()]

    final_url = ""
    if scene_clips:
        final_url = merge_scenes(scene_clips, project_id)

    # Update project
    from database.models import Project
    from sqlalchemy import select
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project:
        project.final_video_url = final_url if final_url else None
        project.status = "completed"
        await db.commit()

    return final_url


async def regenerate_single_scene(db: AsyncSession, scene_id: int) -> dict:
    """Regenerate a single scene's visual, voice, and video without touching others."""
    scene = await get_scene(db, scene_id)
    if not scene:
        return {"error": "Scene not found"}

    # Regenerate visual
    visual_data = await generate_visual(
        prompt=scene.visual_prompt or f"Illustration for: {scene.scene_title}",
        scene_index=scene.scene_index,
        project_id=scene.project_id,
    )
    if isinstance(visual_data, dict):
        scene.image_url = visual_data.get("image_url")
    else:
        scene.image_url = visual_data

    # Regenerate voice
    audio_url = await generate_voice(
        text=scene.script or scene.scene_title,
        scene_index=scene.scene_index,
        project_id=scene.project_id,
        tone=scene.voice_tone,
    )
    scene.audio_url = audio_url

    # Rebuild scene video
    video_url = await build_scene_video(
        image_path=scene.image_url,
        audio_path=audio_url,
        scene_index=scene.scene_index,
        project_id=scene.project_id,
        duration=scene.duration,
        animation_type=scene.animation_type or "zoom",
        motion_direction=scene.motion_direction or "",
    )
    scene.video_clip = video_url
    scene.status = "completed"

    await db.commit()
    await db.refresh(scene)

    return {
        "scene_id": scene.id,
        "image_url": scene.image_url,
        "audio_url": audio_url,
        "video_clip": video_url,
    }
