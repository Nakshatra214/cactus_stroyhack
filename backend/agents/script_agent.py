"""
Script Agent: Converts document content into structured video scenes.
Improved version with smart chunking and important sentence extraction.
"""

import json
import re
from typing import List
from config import settings
from google import genai
import asyncio


SCRIPT_SYSTEM_PROMPT = """
You are an expert educational video script writer.

Convert the provided academic content into a scene-based explainer video.

Rules:
- Each scene explains ONE concept.
- Narration must be concise (1–2 sentences).
- Scenes must follow logical order.
- Highlight the most important concepts.

Constraints:
- Generate 4–8 scenes
- Each scene duration 5–7 seconds

Return ONLY JSON in this format:

{
 "scenes":[
  {
   "scene_id":1,
   "title":"",
   "narration_script":"",
   "visual_prompt":"",
   "voice_tone":"",
   "duration":6,
   "source_reference":"",
   "confidence_score":0.9
  }
 ]
}
"""


# ----------------------------
# TEXT PROCESSING FUNCTIONS
# ----------------------------

def split_into_chunks(text: str, chunk_size: int = 1000) -> List[str]:
    """Split long document into manageable chunks."""
    paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < chunk_size:
            current += " " + para
        else:
            chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return chunks


def extract_key_sentences(text: str) -> str:
    """Extract important sentences using simple keyword heuristics."""
    sentences = re.split(r"(?<=[.!?])\s+", text)

    keywords = [
        "important",
        "significant",
        "key",
        "method",
        "result",
        "model",
        "system",
        "algorithm",
        "approach",
        "ai",
        "machine learning",
        "neural network",
    ]

    scored = []

    for s in sentences:
        score = sum(k in s.lower() for k in keywords)
        scored.append((score, s))

    scored.sort(reverse=True)

    best = [s for _, s in scored[:2]]

    return " ".join(best) if best else sentences[0]


# ----------------------------
# MAIN SCRIPT GENERATOR
# ----------------------------

async def generate_script(content: str) -> dict:
    if settings.OPENAI_API_KEY:
        return await generate_script_with_llm(content)
    elif settings.GEMINI_API_KEY:
        return await generate_script_with_gemini(content)
    return generate_mock_script(content)

async def generate_script_with_gemini(content: str) -> dict:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    chunks = split_into_chunks(content)
    scenes = []
    scene_id = 1

    def call_gemini(chunk):
        return client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[SCRIPT_SYSTEM_PROMPT, chunk],
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
            )
        )

    for chunk in chunks[:8]:
        try:
            response = await asyncio.to_thread(call_gemini, chunk)
            raw = response.text.strip()
            
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                parsed = json.loads(match.group())
                for scene in parsed.get("scenes", []):
                    scene["scene_id"] = scene_id
                    scenes.append(scene)
                    scene_id += 1
        except Exception as e:
            print(f"[ScriptAgent] Gemini generation failed: {e}")
            pass

    if not scenes:
        return generate_mock_script(content)

    return {"scenes": scenes}


# ----------------------------
# LLM VERSION
# ----------------------------

async def generate_script_with_llm(content: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    chunks = split_into_chunks(content)

    scenes = []
    scene_id = 1

    for chunk in chunks[:8]:

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {"role": "user", "content": chunk},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        raw = response.choices[0].message.content.strip()

        match = re.search(r"\{[\s\S]*\}", raw)

        if match:
            try:
                parsed = json.loads(match.group())
                for scene in parsed.get("scenes", []):
                    scene["scene_id"] = scene_id
                    scenes.append(scene)
                    scene_id += 1
            except:
                pass

    return {"scenes": scenes[:8]}


# ----------------------------
# MOCK VERSION (No API)
# ----------------------------

def generate_mock_script(content: str) -> dict:
    chunks = split_into_chunks(content)

    scenes = []

    for i, chunk in enumerate(chunks[:6]):
        key_sentence = extract_key_sentences(chunk)

        scenes.append({
            "scene_id": i + 1,
            "title": f"Scene {i+1}: Key Concept",
            "narration_script": key_sentence,
            "visual_prompt": f"Educational illustration explaining: {key_sentence}",
            "voice_tone": "educational",
            "duration": 6,
            "source_reference": f"Section derived from chunk {i+1}",
            "confidence_score": 0.85
        })

    return {"scenes": scenes}