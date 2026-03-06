import os
import random
import shutil

# Setup FFmpeg for MoviePy BEFORE importing moviepy.editor
_system_ffmpeg = shutil.which("ffmpeg")
if _system_ffmpeg:
    os.environ["IMAGEIO_FFMPEG_EXE"] = _system_ffmpeg
else:
    from config import PROJECT_ROOT
    # Navigate up from backend to root, then to ffmpeg_extracted
    os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(os.path.dirname(PROJECT_ROOT), "ffmpeg_extracted", "bin", "ffmpeg.exe")

from moviepy.editor import ImageClip, CompositeVideoClip
from moviepy.video.fx.all import resize

async def animate_scene(image_path: str, duration: float = 6.0, animation_type: str = None):
    """Animate a static image into a video clip with pan/zoom effects."""
    clip = ImageClip(image_path).set_duration(duration)
    
    effects = ["zoom", "pan_left", "pan_right"]
    effect = animation_type if animation_type and animation_type in effects else random.choice(effects)

    if effect == "zoom":
        clip = clip.fx(resize, lambda t: 1 + 0.08 * t)
        clip = clip.set_position('center')
    elif effect == "pan_left":
        clip = clip.set_position(lambda t: (int(-50 * t), 'center'))
    elif effect == "pan_right":
        clip = clip.set_position(lambda t: (int(50 * t), 'center'))

    # Wrap in CompositeVideoClip explicitly sized to standard 720p HD frame
    animated = CompositeVideoClip([clip], size=(1280, 720))
    return animated
