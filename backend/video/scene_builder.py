"""
Scene Builder: Combines image + audio into an animated scene video clip using MoviePy.
"""
import os
import uuid
import asyncio
import tempfile
from typing import List, Tuple

from config import settings
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
from video.scene_animator import animate_scene

async def build_scene_video(image_path: str, audio_path: str,
                       scene_index: int, project_id: int,
                       duration: float = 6.0, animation_type: str = "zoom",
                       motion_direction: str = "",
                       narration_script: str = "",
                       text_overlay: str = "") -> str:
    return await asyncio.to_thread(
        _build_scene_video_sync,
        image_path,
        audio_path,
        scene_index,
        project_id,
        duration,
        animation_type,
        motion_direction,
        narration_script,
        text_overlay,
    )


def _build_scene_video_sync(image_path: str, audio_path: str,
                       scene_index: int, project_id: int,
                       duration: float = 6.0, animation_type: str = "zoom",
                       motion_direction: str = "",
                       narration_script: str = "",
                       text_overlay: str = "") -> str:
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

    temp_files: List[str] = []
    animated_clip = None
    final_clip = None
    audio_clip = None
    overlay_clips: List = []

    try:
        requested_duration = max(float(duration or 0), 1.0)
        effective_duration = requested_duration

        if audio_local and os.path.exists(audio_local):
            audio_clip = AudioFileClip(audio_local)
            if audio_clip.duration:
                effective_duration = max(requested_duration, float(audio_clip.duration))

        animated_clip = animate_scene(
            image_local,
            effective_duration,
            animation_type=animation_type,
            motion_direction=motion_direction,
        )

        narration_text = _clean_text(narration_script) or _clean_text(text_overlay)
        if narration_text:
            avatar_path = _create_avatar_overlay()
            temp_files.append(avatar_path)
            avatar_clip = ImageClip(avatar_path).with_duration(effective_duration).with_position((28, 470))
            overlay_clips.append(avatar_clip)

            caption_frames = _build_word_caption_frames(narration_text, effective_duration)
            for frame_path, start, span in caption_frames:
                temp_files.append(frame_path)
                caption_clip = (
                    ImageClip(frame_path)
                    .with_start(start)
                    .with_duration(span)
                    .with_position(("center", 520))
                )
                overlay_clips.append(caption_clip)

        if overlay_clips:
            final_clip = CompositeVideoClip([animated_clip, *overlay_clips], size=(1280, 720)).with_duration(effective_duration)
        else:
            final_clip = animated_clip

        if audio_clip:
            final_clip = final_clip.with_audio(audio_clip)

        # Write out
        final_clip.write_videofile(
            filepath,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        if os.path.exists(filepath):
            return f"/storage/videos/{filename}"
        return ""

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[SceneBuilder] Error for scene {scene_index}: {e}")
        return ""
    finally:
        for clip in overlay_clips:
            try:
                clip.close()
            except Exception:
                pass
        if final_clip is not None:
            try:
                final_clip.close()
            except Exception:
                pass
        if animated_clip is not None:
            try:
                animated_clip.close()
            except Exception:
                pass
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

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


def _clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.replace("\n", " ").split()).strip()


def _create_avatar_overlay() -> str:
    width, height = 220, 220
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=42,
        fill=(12, 20, 40, 205),
        outline=(92, 128, 255, 235),
        width=4,
    )

    # Face
    draw.ellipse((60, 28, 160, 128), fill=(255, 222, 188, 255))
    # Hair
    draw.ellipse((55, 20, 165, 90), fill=(28, 41, 74, 255))
    # Eyes
    draw.ellipse((88, 66, 98, 76), fill=(28, 32, 48, 255))
    draw.ellipse((122, 66, 132, 76), fill=(28, 32, 48, 255))
    # Smile
    draw.arc((92, 80, 128, 110), start=12, end=168, fill=(28, 32, 48, 255), width=3)
    # Body
    draw.rounded_rectangle((50, 120, 170, 210), radius=28, fill=(66, 108, 242, 255))

    fd, file_path = tempfile.mkstemp(prefix="storyhack_avatar_", suffix=".png")
    os.close(fd)
    image.save(file_path, "PNG")
    return file_path


def _build_word_caption_frames(narration_text: str, total_duration: float) -> List[Tuple[str, float, float]]:
    words = [w for w in narration_text.split(" ") if w]
    if not words:
        return []

    frame_count = len(words)
    frame_duration = max(total_duration / frame_count, 0.12)
    frames: List[Tuple[str, float, float]] = []

    for index in range(frame_count):
        frame_path = _render_caption_frame(words, index)
        start = index * frame_duration
        if index == frame_count - 1:
            span = max(total_duration - start, frame_duration)
        else:
            span = frame_duration
        frames.append((frame_path, start, span))

    return frames


def _render_caption_frame(words: List[str], active_index: int) -> str:
    width, height = 1120, 165
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=24,
        fill=(8, 10, 20, 205),
        outline=(76, 95, 142, 220),
        width=2,
    )

    font = _load_font(42)
    _draw_wrapped_words(
        draw=draw,
        words=words,
        active_index=active_index,
        font=font,
        left=28,
        top=22,
        right=width - 28,
        bottom=height - 22,
    )

    fd, file_path = tempfile.mkstemp(prefix="storyhack_caption_", suffix=".png")
    os.close(fd)
    image.save(file_path, "PNG")
    return file_path


def _draw_wrapped_words(
    draw: ImageDraw.ImageDraw,
    words: List[str],
    active_index: int,
    font: ImageFont.ImageFont,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> None:
    max_width = max(right - left, 1)
    line_height = _font_height(font) + 10
    max_lines = max(1, (bottom - top) // line_height)
    line_count = 1

    x = left
    y = top

    for index, word in enumerate(words):
        token = f"{word} " if index < len(words) - 1 else word
        token_width = _text_width(draw, token, font)

        if x > left and x + token_width > left + max_width:
            line_count += 1
            if line_count > max_lines:
                break
            x = left
            y += line_height

        draw.text((x, y), token, fill=_word_color(index, active_index), font=font)
        x += token_width


def _word_color(index: int, active_index: int) -> Tuple[int, int, int, int]:
    if index < active_index:
        return (235, 241, 255, 255)
    if index == active_index:
        return (255, 214, 76, 255)
    return (163, 173, 194, 230)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    if hasattr(draw, "textlength"):
        return int(draw.textlength(text, font=font))
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0])
    return int(len(text) * 12)


def _font_height(font: ImageFont.ImageFont) -> int:
    if hasattr(font, "size"):
        return int(getattr(font, "size"))
    bbox = font.getbbox("Ag")
    return int(bbox[3] - bbox[1])


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]

    for font_path in candidates:
        if not font_path:
            continue
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

