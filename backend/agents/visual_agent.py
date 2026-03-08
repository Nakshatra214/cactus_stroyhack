"""
Visual Agent: Generates images for each scene using Stability AI or creates placeholders.
"""
import os
import uuid
import asyncio
import httpx
from PIL import Image, ImageDraw, ImageFont
from config import settings
from google import genai


async def generate_visual(prompt: str, scene_index: int, project_id: int):
    """Generate a visual image for a scene. Returns the image metadata dict or URL."""
    if settings.GEMINI_API_KEY:
        # Gemini image generation is synchronous; run it in a worker thread
        # so API polling endpoints remain responsive.
        return await asyncio.to_thread(_generate_with_gemini, prompt, scene_index, project_id)
    elif settings.STABILITY_API_KEY:
        return await _generate_with_stability(prompt, scene_index, project_id)
    else:
        return _generate_placeholder(prompt, scene_index, project_id)


def _generate_with_gemini(prompt: str, scene_index: int, project_id: int):
    """Use Google Gemini API to generate an image."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    filename = f"scene_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(settings.MEDIA_DIR, filename)
    
    try:
        # Prepend styles for better scene aesthetics
        enhanced_prompt = f"Clear educational visuals suitable for an explainer video. Avoid abstract descriptions. Focus on diagrams, data visualization, and educational illustrations. {prompt}"
        
        # Generate image using Google Imagen 3 via the Gemini API
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=enhanced_prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/png"
            )
        )
        
        if result.generated_images:
            for generated_image in result.generated_images:
                # Save the image bytes to file
                image_bytes = generated_image.image.image_bytes
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                import random
                return {
                    "image_url": f"/storage/media/{filename}",
                    "animation_type": random.choice(["zoom", "pan_left", "pan_right"]),
                    "duration": 6.0
                }
    except Exception as e:
        print(f"[VisualAgent] Gemini generation failed: {e}")
        
    # Fall back to placeholder if Gemini fails
    return _generate_placeholder(prompt, scene_index, project_id)


async def _generate_with_stability(prompt: str, scene_index: int, project_id: int) -> str:
    """Use Stability AI API to generate an image."""
    filename = f"scene_{project_id}_{scene_index}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(settings.MEDIA_DIR, filename)

    try:
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
                for i, image in enumerate(data["artifacts"]):
                    import base64
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(image["base64"]))
                    
                    import random
                    return {
                        "image_url": f"/storage/media/{filename}",
                        "animation_type": random.choice(["zoom", "pan_left", "pan_right"]),
                        "duration": 6.0
                    }
            else:
                print(f"[VisualAgent] Stability API error: {response.text}")
                return _generate_placeholder(prompt, scene_index, project_id)
                
    except Exception as e:
        print(f"[VisualAgent] Exception calling Stability: {e}")
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

    if not os.path.exists(filepath):
        # Create a blank image with colorful background
        img = Image.new('RGB', (1280, 720), color=(
            hash(prompt) % 256,
            (hash(prompt) // 256) % 256,
            (hash(prompt) // 65536) % 256
        ))
        d = ImageDraw.Draw(img)
        
        # Add text
        try:
            # Try to use a default Windows font
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
            
        # Word-wrap the prompt
        max_chars = 60
        wrapped = prompt[:max_chars * 3]
        if len(prompt) > max_chars * 3:
            wrapped += "..."
            
        lines = [wrapped[i:i+max_chars] for i in range(0, len(wrapped), max_chars)]
        y_text = 360 - (len(lines) * 20)
        
        for line in lines:
            text_width = d.textlength(line, font=font) if hasattr(d, 'textlength') else 400
            d.text(((1280 - text_width) / 2, y_text), line, fill=(255, 255, 255), font=font)
            y_text += 50
            
        img.save(filepath)
    
    import random
    return {
        "image_url": f"/storage/media/{filename}",
        "animation_type": random.choice(["zoom", "pan_left", "pan_right"]),
        "duration": 6.0
    }
