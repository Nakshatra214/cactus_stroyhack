import os
import shutil

# Setup FFmpeg for MoviePy BEFORE importing moviepy
_system_ffmpeg = shutil.which("ffmpeg")
if _system_ffmpeg:
    os.environ["IMAGEIO_FFMPEG_EXE"] = _system_ffmpeg
else:
    from config import PROJECT_ROOT

    os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(
        os.path.dirname(PROJECT_ROOT),
        "ffmpeg_extracted",
        "bin",
        "ffmpeg.exe",
    )

from moviepy import CompositeVideoClip, ImageClip
from moviepy.video.fx.Resize import Resize


def _normalize_effect(animation_type: str, motion_direction: str) -> str:
    raw = (animation_type or "").strip().lower().replace("-", " ").replace("_", " ")
    motion = (motion_direction or "").strip().lower()

    if "left" in motion:
        return "pan_left"
    if "right" in motion:
        return "pan_right"
    if "zoom" in motion:
        return "zoom"

    if raw in {"pan left", "left pan", "pan_left"}:
        return "pan_left"
    if raw in {"pan right", "right pan", "pan_right"}:
        return "pan_right"
    if raw == "zoom":
        return "zoom"

    # Deterministic mapping for currently unsupported effect families.
    if raw == "parallax":
        return "pan_right"
    if raw == "infographic animation":
        return "zoom"
    if raw in {"diagram drawing", "diagram drawing animation"}:
        return "pan_left"

    return "zoom"


def animate_scene(
    image_path: str,
    duration: float = 6.0,
    animation_type: str = "zoom",
    motion_direction: str = "",
):
    """Animate a static image into a video clip with deterministic pan/zoom effects."""
    clip = ImageClip(image_path).with_duration(duration)
    effect = _normalize_effect(animation_type, motion_direction)

    if effect == "zoom":
        clip = clip.with_effects([Resize(lambda t: 1 + 0.08 * t)])
        clip = clip.with_position("center")
    elif effect == "pan_left":
        clip = clip.with_position(lambda t: (int(-50 * t), "center"))
    elif effect == "pan_right":
        clip = clip.with_position(lambda t: (int(50 * t), "center"))

    return CompositeVideoClip([clip], size=(1280, 720))
