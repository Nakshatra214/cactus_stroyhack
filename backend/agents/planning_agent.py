"""
Planning Agent: Generates a strict video_plan JSON for educational explainer videos.
"""
import json
import re
import asyncio
from typing import Any, Dict, List

from config import settings
from google import genai


PLANNING_SYSTEM_PROMPT = """
You are an expert educational video director, script writer, and animation designer.

Convert academic/research content into a complete explainer video plan.

Requirements:
- Extract the most important ideas from the document.
- Organize ideas into a natural learning progression.
- Each scene explains exactly one concept.
- Narration per scene must be concise (1-2 sentences).
- Scene duration must be 5-10 seconds.
- Prefer educational diagrams, data visualizations, flat design illustrations, minimal infographic style.
- Avoid abstract visuals and photorealistic imagery unless clearly needed by the content.
- Every scene must include cinematic motion planning.

Return ONLY valid JSON in this exact shape:
{
  "video_plan": {
    "title": "",
    "total_scenes": 0,
    "estimated_video_duration": "",
    "visual_style": "educational infographic",
    "scenes": [
      {
        "scene_id": 1,
        "title": "",
        "narration_script": "",
        "visual_description": "",
        "visual_prompt": "",
        "camera_shot": "",
        "animation_type": "",
        "motion_direction": "",
        "visual_layers": [],
        "text_overlay": "",
        "transition": "",
        "duration": 6,
        "source_reference": "",
        "confidence_score": 0.95
      }
    ]
  }
}
"""


def _extract_json_dict(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()

    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        text = brace.group(0)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _generate_mock_plan(content: str, target_scene_count: int) -> Dict[str, Any]:
    sentences = _split_sentences(content)
    if not sentences:
        sentences = ["This section introduces the main topic."]

    scenes: List[Dict[str, Any]] = []
    for i in range(target_scene_count):
        sent = sentences[i % len(sentences)]
        short_title = f"Concept {i + 1}"
        duration = 6 + (i % 3)
        scenes.append(
            {
                "scene_id": i + 1,
                "title": short_title,
                "narration_script": sent,
                "visual_description": f"Infographic panel explaining {short_title.lower()} with labeled elements.",
                "visual_prompt": f"Educational infographic, flat design, 16:9, explain {sent}",
                "camera_shot": "medium shot",
                "animation_type": ["zoom", "pan_left", "pan_right", "parallax"][i % 4],
                "motion_direction": ["slow zoom in", "pan left", "pan right", "subtle parallax drift"][i % 4],
                "visual_layers": ["background gradient", "diagram", "labels"],
                "text_overlay": short_title,
                "transition": "fade",
                "duration": duration,
                "source_reference": f"Derived from source segment {i + 1}",
                "confidence_score": 0.86,
            }
        )

    return {
        "video_plan": {
            "title": "Research Explainer",
            "total_scenes": len(scenes),
            "estimated_video_duration": f"{sum(s['duration'] for s in scenes)} seconds",
            "visual_style": "educational infographic",
            "scenes": scenes,
        }
    }


async def generate_video_plan(content: str, target_scene_count: int) -> Dict[str, Any]:
    user_prompt = (
        f"Target number of scenes: {target_scene_count}\n\n"
        "Convert the following content into the required JSON video_plan.\n\n"
        f"CONTENT:\n{content[:24000]}"
    )

    if settings.OPENAI_API_KEY:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2200,
                ),
                timeout=45,
            )
            parsed = _extract_json_dict(response.choices[0].message.content or "")
            if parsed:
                return parsed
        except Exception as e:
            print(f"[PlanningAgent] OpenAI generation failed: {e}")

    if settings.GEMINI_API_KEY:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        try:
            def call_gemini():
                return client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[PLANNING_SYSTEM_PROMPT, user_prompt],
                    config=genai.types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    ),
                )

            response = await asyncio.wait_for(asyncio.to_thread(call_gemini), timeout=45)
            parsed = _extract_json_dict(getattr(response, "text", "") or "")
            if parsed:
                return parsed
        except Exception as e:
            print(f"[PlanningAgent] Gemini generation failed: {e}")

    return _generate_mock_plan(content, target_scene_count)
