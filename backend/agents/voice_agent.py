"""
Voice Agent: Generates voiceover audio for scene narration using OpenAI TTS or edge-tts.
"""
import os
import uuid
import edge_tts
from config import settings


async def generate_voice(text: str, scene_index: int, project_id: int,
                         voice: str = None, tone: str = "neutral") -> str:
    """Generate voiceover audio for a scene. Returns the audio file path."""
    if settings.OPENAI_API_KEY:
        return await _generate_with_openai_tts(text, scene_index, project_id, voice)
    else:
        return await _generate_with_edge_tts(text, scene_index, project_id, tone)


async def _generate_with_openai_tts(text: str, scene_index: int, project_id: int,
                                     voice: str = None) -> str:
    """Use OpenAI TTS to generate voiceover."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    filename = f"voice_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    response = await client.audio.speech.create(
        model=settings.OPENAI_TTS_MODEL,
        voice=voice or settings.OPENAI_TTS_VOICE,
        input=text,
    )

    with open(filepath, "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)

    return f"/storage/media/{filename}"


async def _generate_with_edge_tts(text: str, scene_index: int, project_id: int, tone: str = "neutral") -> str:
    """Use edge-tts to generate high-quality free voiceover."""
    filename = f"voice_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    # Map tones to specific voices (edge-tts has many voices, we'll pick good English ones)
    voice_mapping = {
        "neutral": "en-US-ChristopherNeural",   # Male, clear
        "professional": "en-US-SteffanNeural",  # Male, professional
        "friendly": "en-US-AriaNeural",         # Female, friendly
        "enthusiastic": "en-US-GuyNeural",      # Male, energetic
        "calm": "en-GB-SoniaNeural",            # UK Female, expressive
    }
    
    selected_voice = voice_mapping.get(tone, "en-US-ChristopherNeural")
    
    # Create communicate object
    communicate = edge_tts.Communicate(text, selected_voice)
    
    # Generate and save
    await communicate.save(filepath)
    
    return f"/storage/media/{filename}"
