"""
Script Agent: Converts document content into structured video scenes.
Uses OpenAI/LangChain to summarize, segment, and generate scene scripts.
"""
import json
import re
from typing import Optional
from config import settings


SCRIPT_SYSTEM_PROMPT = """You are an expert educational video script writer.

Your task is to convert structured content (research paper, lecture notes, or report) into a scene-based explainer video.

Rules:
- Output must be structured for a video editor system.
- Each scene should represent ONE clear idea.
- Maximum scene duration: 5–7 seconds.
- Avoid generic statements.
- Ensure technical accuracy.
- Maintain grounding in the source content.

For each scene generate:
1. Scene title
2. Narration script
3. Visual prompt (for image/video generation)
4. Source reference (which section generated this)
5. Estimated duration (seconds)
6. Voice tone
7. Confidence score (0–1)

Constraints:
- 4–8 scenes maximum
- Each narration: 1–2 sentences
- Visual prompt must describe a clear visual concept

Return ONLY JSON.

Output format:
{
 "scenes":[
  {
   "scene_id":1,
   "title":"",
   "narration_script":"",
   "visual_prompt":"",
   "voice_tone":"",
   "duration":5,
   "source_reference":"",
   "confidence_score":0.95
  }
 ]
}"""


async def generate_script(content: str) -> dict:
    """Generate a structured video script from document content."""
    if settings.OPENAI_API_KEY:
        return await _generate_with_openai(content)
    else:
        return _generate_mock_script(content)


async def _generate_with_openai(content: str) -> dict:
    """Use OpenAI to generate the script."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Truncate content if too long
    max_chars = 12000
    truncated = content[:max_chars] if len(content) > max_chars else content

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Convert this content into a video script:\n\n{truncated}"},
        ],
        temperature=0.7,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _generate_mock_script(content)


def _generate_mock_script(content: str) -> dict:
    """Generate a mock script when no API key is available."""
    # Split content into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    if not paragraphs:
        paragraphs = [content[:500]]

    # Create scenes from paragraphs (max 6 scenes)
    scenes = []
    chunk_size = max(1, len(paragraphs) // 6)

    for i in range(0, min(len(paragraphs), 6 * chunk_size), chunk_size):
        chunk = ' '.join(paragraphs[i:i + chunk_size])
        if len(chunk) > 300:
            chunk = chunk[:300] + '...'

        scene_num = len(scenes) + 1
        scenes.append({
            "scene_id": scene_num,
            "title": f"Scene {scene_num}: Key Concepts",
            "narration_script": chunk if len(chunk) > 20 else f"This section covers important concepts from the source material. {chunk}",
            "visual_prompt": f"Professional educational illustration showing concepts related to: {chunk[:100]}. Clean modern design with infographics.",
            "voice_tone": "neutral",
            "duration": 6,
            "source_reference": f"Based on paragraph {i + 1} of the original content",
            "confidence_score": round(0.75 + (scene_num * 0.03), 2),
        })

        if len(scenes) >= 6:
            break

    if not scenes:
        scenes = [{
            "scene_id": 1,
            "title": "Introduction",
            "narration_script": "Welcome to this video presentation covering the key topics from the uploaded content.",
            "visual_prompt": "Modern title slide with abstract geometric background in blue and purple gradients",
            "voice_tone": "professional",
            "duration": 5,
            "source_reference": "Generated introduction",
            "confidence_score": 0.95,
        }]

    return {"scenes": scenes}
