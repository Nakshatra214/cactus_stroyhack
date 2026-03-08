"""
Video Merger: Concatenates animated scene clips into a final video using MoviePy.
"""
import os
import uuid
from typing import List
from config import settings
from moviepy import VideoFileClip, concatenate_videoclips

def merge_scenes(scene_clips: List[str], project_id: int) -> str:
    """Merge multiple scene video clips into a single final video using MoviePy concat."""
    filename = f"final_{project_id}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(settings.VIDEO_DIR, filename)

    valid_clips = []
    for clip in scene_clips:
        if not clip: continue
        local_path = _resolve_path(clip)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024:
            valid_clips.append(local_path)

    if not valid_clips:
        return ""

    if len(valid_clips) == 1:
        import shutil
        shutil.copy2(valid_clips[0], filepath)
        return f"/storage/videos/{filename}"

    try:
        clips = []
        for p in valid_clips:
            clips.append(VideoFileClip(p))

        final = concatenate_videoclips(clips, method="compose")

        final.write_videofile(
            filepath,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        for clip in clips:
            clip.close()
        final.close()

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
            return f"/storage/videos/{filename}"
        return ""

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[VideoMerger] Merge error: {e}")
        return ""

def _resolve_path(url_path: str) -> str:
    """Convert a URL path like /storage/videos/foo.mp4 to an absolute filesystem path."""
    if url_path.startswith("/storage/media/"):
        filename = url_path.replace("/storage/media/", "")
        return os.path.join(settings.MEDIA_DIR, filename)
    elif url_path.startswith("/storage/videos/"):
        filename = url_path.replace("/storage/videos/", "")
        return os.path.join(settings.VIDEO_DIR, filename)
    elif url_path.startswith("/storage/"):
        from config import PROJECT_ROOT
        return os.path.join(PROJECT_ROOT, url_path[1:])
    return url_path

