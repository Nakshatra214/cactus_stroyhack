"""
Visual Agent: Generates images for each scene using Stability AI or creates placeholders.
"""
import os
import uuid
import httpx
from PIL import Image, ImageDraw, ImageFont
from config import settings


async def generate_visual(prompt: str, scene_index: int, project_id: int) -> str:
    """Generate a visual image for a scene. Returns the image file path."""
    if settings.STABILITY_API_KEY:
        return await _generate_with_stability(prompt, scene_index, project_id)
    else:
        return _generate_placeholder(prompt, scene_index, project_id)


async def _generate_with_stability(prompt: str, scene_index: int, project_id: int) -> str:
    """Use Stability AI API to generate an image."""
    filename = f"scene_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.STABILITY_API_URL,
            headers={
                "Authorization": f"Bearer {settings.STABILITY_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "text_prompts": [{"text": prompt, "weight": 1}],
                "cfg_scale": 7,
                "height": 720,
                "width": 1280,
                "steps": 30,
                "samples": 1,
            },
        )

        if response.status_code == 200:
            data = response.json()
            import base64
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            with open(filepath, "wb") as f:
                f.write(image_data)
            return f"/storage/media/{filename}"
        else:
            return _generate_placeholder(prompt, scene_index, project_id)


def _generate_placeholder(prompt: str, scene_index: int, project_id: int) -> str:
    """Generate a styled placeholder image when no API key is available."""
    filename = f"scene_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    # Create a gradient-style placeholder
    width, height = 1280, 720
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    # Create gradient background
    colors = [
        [(25, 25, 112), (72, 61, 139)],   # Dark blue to purple
        [(0, 100, 0), (34, 139, 34)],       # Dark green to green
        [(139, 0, 0), (205, 92, 92)],       # Dark red to coral
        [(0, 0, 139), (0, 139, 139)],       # Blue to teal
        [(75, 0, 130), (138, 43, 226)],    # Indigo to violet
        [(0, 128, 128), (0, 206, 209)],    # Teal to dark turquoise
    ]
    c1, c2 = colors[scene_index % len(colors)]

    for y in range(height):
        r = int(c1[0] + (c2[0] - c1[0]) * y / height)
        g = int(c1[1] + (c2[1] - c1[1]) * y / height)
        b = int(c1[2] + (c2[2] - c1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add text
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 22)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = font_large

    title = f"Scene {scene_index + 1}"
    draw.text((width // 2 - 100, height // 2 - 60), title, fill="white", font=font_large)

    # Word-wrap the prompt
    max_chars = 60
    wrapped = prompt[:max_chars * 3]
    lines = [wrapped[i:i + max_chars] for i in range(0, len(wrapped), max_chars)]
    y_offset = height // 2 + 10
    for line in lines[:3]:
        draw.text((60, y_offset), line, fill=(200, 200, 200), font=font_small)
        y_offset += 30

    img.save(filepath, "PNG")
    return f"/storage/media/{filename}"
