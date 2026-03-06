"""
Voice Service: Wraps voice agent with file storage handling.
"""
from agents.voice_agent import generate_voice


async def generate_scene_voice(text: str, scene_index: int, project_id: int,
                                voice: str = None, tone: str = "neutral") -> str:
    """Generate voiceover for a scene narration."""
    return await generate_voice(
        text=text,
        scene_index=scene_index,
        project_id=project_id,
        voice=voice,
        tone=tone,
    )
