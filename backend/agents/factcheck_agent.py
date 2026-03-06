"""
Fact Check Agent: Validates generated script against source content.
Detects hallucinations and provides confidence scores.
"""
import re
from config import settings


async def fact_check_scene(narration: str, source_content: str,
                           source_reference: str = "") -> dict:
    """Check a scene's narration against source content.
    Returns confidence score and reasoning."""
    if settings.OPENAI_API_KEY:
        return await _check_with_openai(narration, source_content, source_reference)
    else:
        return _check_mock(narration, source_content)


async def _check_with_openai(narration: str, source_content: str,
                              source_reference: str) -> dict:
    """Use OpenAI to fact-check the narration."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""Compare the following narration against the source content.
Determine if the narration is faithful to the source.

Source Content:
{source_content[:5000]}

Narration:
{narration}

Source Reference: {source_reference}

Respond in JSON format:
{{
    "confidence_score": 0.0 to 1.0,
    "is_faithful": true/false,
    "reasoning": "explanation",
    "source_reference": "which part of the source this relates to",
    "potential_issues": ["list of any issues found"]
}}"""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a fact-checking AI. Respond only in valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if json_match:
        raw = json_match.group(1).strip()

    import json
    try:
        return json.loads(raw)
    except Exception:
        return _check_mock(narration, source_content)


def _check_mock(narration: str, source_content: str) -> dict:
    """Mock fact-check using simple keyword overlap."""
    # Simple keyword overlap heuristic
    narration_words = set(re.findall(r'\b\w{4,}\b', narration.lower()))
    source_words = set(re.findall(r'\b\w{4,}\b', source_content.lower()))

    if not narration_words:
        overlap = 0.5
    else:
        overlap = len(narration_words & source_words) / len(narration_words)

    confidence = min(0.95, max(0.6, overlap * 1.2))

    return {
        "confidence_score": round(confidence, 2),
        "is_faithful": confidence > 0.7,
        "reasoning": f"Keyword overlap analysis: {len(narration_words & source_words)}/{len(narration_words)} key terms found in source.",
        "source_reference": "Analyzed against full source content",
        "potential_issues": [] if confidence > 0.7 else ["Some narration terms not found in source material"],
    }
