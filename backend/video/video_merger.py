"""
Video Merger: Concatenates individual scene clips into a final video.
Skips merging if FFmpeg is not available.
"""
import os
import uuid
from typing import List
from config import settings


def merge_scenes(scene_clips: List[str], project_id: int) -> str:
    """Merge multiple scene video clips into a single final video.
    Returns empty string if no valid clips or FFmpeg is unavailable."""
    filename = f"final_{project_id}_{uuid.uuid4().hex[:8]}.mp4"
    filepath = os.path.join(settings.VIDEO_DIR, filename)

    # Resolve paths and filter valid clips
    local_clips = [_resolve_path(clip) for clip in scene_clips if clip and clip.strip()]
    valid_clips = [c for c in local_clips if os.path.exists(c) and os.path.getsize(c) > 1024]

    if not valid_clips:
        print(f"[VideoMerger] No valid scene clips to merge for project {project_id}. "
              f"Frontend will use image+audio preview.")
        return ""

    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        clips = []
        for clip_path in valid_clips:
            try:
                clip = VideoFileClip(clip_path)
                clips.append(clip)
            except Exception as e:
                print(f"[VideoMerger] Error loading clip {clip_path}: {e}")

        if clips:
            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(
                filepath,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            for clip in clips:
                clip.close()
            final.close()
            return f"/storage/videos/{filename}"
        else:
            return ""

    except Exception as e:
        print(f"[VideoMerger] Merge error: {e}")
        return ""


def _resolve_path(url_path: str) -> str:
    """Convert URL path to local filesystem path."""
    if url_path.startswith("/storage/"):
        return url_path[1:]
    return url_path
