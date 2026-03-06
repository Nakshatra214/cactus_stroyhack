"""
Scene Builder: Combines image + audio into a scene video clip using MoviePy.
Falls back to image+audio preview if FFmpeg is not available.
"""
import os
import uuid
import subprocess
from config import settings


def is_ffmpeg_available() -> bool:
    """Check if FFmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


_FFMPEG_AVAILABLE = is_ffmpeg_available()


def build_scene_video(image_path: str, audio_path: str,
                      scene_index: int, project_id: int,
                      duration: float = 5.0) -> str:
    """Build a single scene video from an image and audio file.
    If FFmpeg is not available, returns None and the frontend shows image+audio preview."""

    if not _FFMPEG_AVAILABLE:
        print(f"[SceneBuilder] FFmpeg not found — skipping video build for scene {scene_index}. "
              f"Image and audio will be used for preview.")
        return ""

    filename = f"clip_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(settings.VIDEO_DIR, filename)

    # Resolve storage paths (remove /storage/ prefix for local file access)
    image_local = _resolve_path(image_path)
    audio_local = _resolve_path(audio_path)

    try:
        from moviepy.editor import ImageClip, AudioFileClip

        # Load audio to get duration
        audio_clip = AudioFileClip(audio_local)
        actual_duration = max(duration, audio_clip.duration)

        # Create video from image with audio
        image_clip = (
            ImageClip(image_local)
            .set_duration(actual_duration)
            .resize((1280, 720))
            .set_fps(24)
        )

        video = image_clip.set_audio(audio_clip)
        video.write_videofile(
            filepath,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        audio_clip.close()
        image_clip.close()

        return f"/storage/videos/{filename}"

    except Exception as e:
        print(f"[SceneBuilder] MoviePy error for scene {scene_index}: {e}")
        return ""


def _resolve_path(url_path: str) -> str:
    """Convert URL path to local filesystem path."""
    if url_path.startswith("/storage/"):
        return url_path[1:]  # Remove leading /
    return url_path
