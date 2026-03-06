"""
Edit Agent: Regenerates a single scene based on user instructions while maintaining context.
"""
import json
import re
from config import settings


EDIT_SYSTEM_PROMPT = """You are assisting in editing a single scene of an educational video.

Your task is to regenerate ONLY this scene while keeping the context of the entire video consistent.

Rules:
- Maintain topic consistency
- Improve clarity
- Keep narration concise
- Keep duration under 7 seconds
- Ensure visuals clearly represent the concept

Return JSON only.
"""

async def agentic_edit_scene(current_scene_json: str, user_instruction: str) -> dict:
    """Use OpenAI to modify a scene based on a user instruction."""
    if not settings.OPENAI_API_KEY:
        # Mock behavior for testing without an API key
        mock = json.loads(current_scene_json)
        mock["narration_script"] = f"[Mock Edited: {user_instruction}] {mock.get('narration_script', '')}"
        return mock

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = f"""Scene to regenerate:\n{current_scene_json}\n\nUser changes:\n{user_instruction}"""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": EDIT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[EditAgent] Failed to decode JSON: {e}")
        return json.loads(current_scene_json)
