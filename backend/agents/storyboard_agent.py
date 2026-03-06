"""
Storyboard Agent: Converts generated scenes into detailed visual storyboard frames.
"""
import json
import re
from config import settings


STORYBOARD_SYSTEM_PROMPT = """You are a storyboard designer for educational videos.

Given a set of scenes, generate a storyboard describing how each scene should visually appear.

Each scene must include:
- camera shot type
- visual composition
- animation style
- text overlays
- transition

Return JSON.

Output format:
{
 "storyboard":[
  {
   "scene_id":1,
   "visual_description":"",
   "camera_shot":"",
   "animation_style":"",
   "text_overlay":"",
   "transition":""
  }
 ]
}"""

async def generate_storyboard(scenes_json: str) -> dict:
    """Use OpenAI to generate a storyboard from a list of scenes."""
    if not settings.OPENAI_API_KEY:
        # Mock behavior
        scenes = json.loads(scenes_json).get("scenes", [])
        return {
            "storyboard": [
                {
                    "scene_id": s.get("scene_id", i + 1),
                    "visual_description": f"Mock visual for {s.get('title', 'scene')}",
                    "camera_shot": "Wide establishing shot",
                    "animation_style": "Smooth medical infographic animation",
                    "text_overlay": s.get("title", ""),
                    "transition": "Fade in",
                }
                for i, s in enumerate(scenes)
            ]
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = f"""Scenes:\n{scenes_json}"""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[StoryboardAgent] Failed to decode JSON: {e}")
        return {"storyboard": []}
