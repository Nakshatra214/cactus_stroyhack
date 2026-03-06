"""
Voice Agent: Generates voiceover audio for scene narration using OpenAI TTS or mock.
"""
import os
import uuid
import struct
import math
from config import settings


async def generate_voice(text: str, scene_index: int, project_id: int,
                         voice: str = None, tone: str = "neutral") -> str:
    """Generate voiceover audio for a scene. Returns the audio file path."""
    if settings.OPENAI_API_KEY:
        return await _generate_with_openai_tts(text, scene_index, project_id, voice)
    else:
        return _generate_mock_audio(text, scene_index, project_id)


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


def _generate_mock_audio(text: str, scene_index: int, project_id: int) -> str:
    """Generate a silent WAV file as placeholder when no API key is available."""
    filename = f"voice_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    # Estimate duration from text length (roughly 150 words per minute)
    word_count = len(text.split())
    duration = max(3.0, min(word_count / 2.5, 30.0))

    # Generate a simple WAV file with a gentle tone
    sample_rate = 22050
    num_samples = int(sample_rate * duration)

    # Create WAV header
    with open(filepath, 'wb') as f:
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = num_samples * block_align

        # WAV header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))  # PCM
        f.write(struct.pack('<H', num_channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits_per_sample))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))

        # Generate a gentle sine wave (440Hz at low volume) fading in/out
        for i in range(num_samples):
            t = i / sample_rate
            # Envelope: fade in first 0.5s, fade out last 0.5s
            envelope = 1.0
            if t < 0.5:
                envelope = t / 0.5
            elif t > duration - 0.5:
                envelope = (duration - t) / 0.5
            sample = int(800 * envelope * math.sin(2 * math.pi * 220 * t))
            f.write(struct.pack('<h', max(-32768, min(32767, sample))))

    return f"/storage/media/{filename}"
