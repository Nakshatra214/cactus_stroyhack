"""
Script Agent: Converts document content into structured video scenes.
Uses OpenAI/LangChain to summarize, segment, and generate scene scripts.
"""
import json
import re
from typing import Optional
from config import settings


SCRIPT_SYSTEM_PROMPT = """You are an expert video script writer. Your task is to convert document content into a structured video script.

Rules:
1. Break the content into 3-8 logical scenes
2. Each scene should be self-contained and flow naturally
3. Write narration in a clear, engaging, conversational tone
4. Create visual prompts that describe what should be shown on screen
5. Include source references indicating which part of the original content each scene is based on
6. Keep each scene narration between 30-100 words

Output ONLY valid JSON in this exact format:
{
  "scenes": [
    {
      "title": "Scene title",
      "narration": "The narration text for this scene",
      "visual_prompt": "A detailed description of the visual to generate",
      "source_reference": "Based on section/paragraph X of the original content",
      "confidence": 0.9
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
            "title": f"Scene {scene_num}: Key Concepts",
            "narration": chunk if len(chunk) > 20 else f"This section covers important concepts from the source material. {chunk}",
            "visual_prompt": f"Professional educational illustration showing concepts related to: {chunk[:100]}. Clean modern design with infographics.",
            "source_reference": f"Based on paragraph {i + 1} of the original content",
            "confidence": round(0.75 + (scene_num * 0.03), 2),
        })

        if len(scenes) >= 6:
            break

    if not scenes:
        scenes = [{
            "title": "Introduction",
            "narration": "Welcome to this video presentation covering the key topics from the uploaded content.",
            "visual_prompt": "Modern title slide with abstract geometric background in blue and purple gradients",
            "source_reference": "Generated introduction",
            "confidence": 0.95,
        }]

    return {"scenes": scenes}
