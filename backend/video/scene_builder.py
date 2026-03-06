"""
Scene Builder: Combines image + audio into an animated scene video clip using MoviePy.
"""
import os
import uuid
from config import settings
from moviepy.editor import AudioFileClip
from video.scene_animator import animate_scene

async def build_scene_video(image_path: str, audio_path: str,
                       scene_index: int, project_id: int,
                       duration: float = 6.0, animation_type: str = "zoom") -> str:
    """Build a single scene video from an image and audio file using MoviePy."""
    if not image_path:
        return ""
        
    filename = f"clip_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(settings.VIDEO_DIR, filename)

    # Resolve storage paths
    image_local = _resolve_path(image_path)
    audio_local = _resolve_path(audio_path) if audio_path else ""

    if not os.path.exists(image_local):
        print(f"[SceneBuilder] Image not found: {image_local}")
        return ""

    try:
        animated_clip = await animate_scene(image_local, duration, animation_type=animation_type)

        if audio_local and os.path.exists(audio_local):
            audio_clip = AudioFileClip(audio_local)
            animated_clip = animated_clip.set_audio(audio_clip)

        # Write out
        animated_clip.write_videofile(
            filepath,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )
        
        # Cleanup memory handlers
        animated_clip.close()

        if os.path.exists(filepath):
            return f"/storage/videos/{filename}"
        return ""

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[SceneBuilder] Error for scene {scene_index}: {e}")
        return ""

def _resolve_path(url_path: str) -> str:
    """Convert a URL path like /storage/media/foo.png to an absolute filesystem path."""
    if url_path.startswith("/storage/media/"):
        filename = url_path.replace("/storage/media/", "")
        return os.path.join(settings.MEDIA_DIR, filename)
    elif url_path.startswith("/storage/videos/"):
        filename = url_path.replace("/storage/videos/", "")
        return os.path.join(settings.VIDEO_DIR, filename)
    elif url_path.startswith("/storage/"):
        # Generic fallback
        from config import PROJECT_ROOT
        return os.path.join(PROJECT_ROOT, url_path[1:])
    return url_path

