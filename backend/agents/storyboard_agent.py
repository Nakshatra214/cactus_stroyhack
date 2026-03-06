"""
Storyboard Agent: Converts generated scenes into detailed visual storyboard frames.
"""
import json
import re
import asyncio
from config import settings


STORYBOARD_SYSTEM_PROMPT = """You are a storyboard designer for educational videos.

Given a set of scenes, generate a storyboard describing how each scene should visually appear.

Each scene must include:
- camera shot type
- visual composition
- animation type
- motion direction
- visual layers
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
   "animation_type":"",
   "motion_direction":"",
   "visual_layers":[],
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
                    "animation_type": "infographic animation",
                    "motion_direction": "slow zoom in",
                    "visual_layers": ["background", "diagram", "labels"],
                    "text_overlay": s.get("title", ""),
                    "transition": "Fade in",
                }
                for i, s in enumerate(scenes)
            ]
        }

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = f"""Scenes:\n{scenes_json}"""

    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            ),
            timeout=35,
        )
    except Exception as e:
        print(f"[StoryboardAgent] LLM generation failed: {e}")
        scenes = json.loads(scenes_json).get("scenes", [])
        return {
            "storyboard": [
                {
                    "scene_id": s.get("scene_id", i + 1),
                    "visual_description": f"Mock visual for {s.get('title', 'scene')}",
                    "camera_shot": "Wide establishing shot",
                    "animation_type": "infographic animation",
                    "motion_direction": "slow zoom in",
                    "visual_layers": ["background", "diagram", "labels"],
                    "text_overlay": s.get("title", ""),
                    "transition": "Fade in",
                }
                for i, s in enumerate(scenes)
            ]
        }

    raw = response.choices[0].message.content.strip()

    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[StoryboardAgent] Failed to decode JSON: {e}")
        return {"storyboard": []}
