"""
Planning Service: Normalizes and validates planning-agent output for downstream pipeline use.
"""
import json
import re
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from agents.factcheck_agent import fact_check_scene
from agents.planning_agent import generate_video_plan
from agents.storyboard_agent import generate_storyboard
from database.models import Scene
from services.scene_service import get_scenes

DEFAULT_VISUAL_STYLE = "educational infographic"
ALLOWED_ANIMATION_TYPES = {
    "zoom",
    "pan_left",
    "pan_right",
    "parallax",
    "infographic animation",
    "diagram drawing animation",
}


def _adaptive_scene_count(content: str) -> int:
    words = len(re.findall(r"\b\w+\b", content or ""))
    if words <= 250:
        return 4
    estimate = int(round(words / 180.0))
    return max(4, min(14, estimate))


def _clamp_duration(value: Any, default: int = 6) -> int:
    try:
        duration = int(round(float(value)))
    except Exception:
        duration = default
    return max(5, min(10, duration))


def _clamp_confidence(value: Any, default: float = 0.85) -> float:
    try:
        score = float(value)
    except Exception:
        score = default
    return max(0.0, min(1.0, round(score, 2)))


def _parse_layers(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
        return [seg.strip() for seg in text.split(",") if seg.strip()]
    return []


def _normalize_animation_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("-", " ").replace("_", " ")

    if text in {"pan left", "left pan"}:
        return "pan_left"
    if text in {"pan right", "right pan"}:
        return "pan_right"
    if text == "diagram drawing":
        return "diagram drawing animation"
    if text == "infographic":
        return "infographic animation"
    if text == "zoom":
        return "zoom"
    if text == "parallax":
        return "parallax"
    if text in ALLOWED_ANIMATION_TYPES:
        return text
    return "zoom"


def _default_motion(animation_type: str) -> str:
    if animation_type == "pan_left":
        return "pan left"
    if animation_type == "pan_right":
        return "pan right"
    if animation_type == "parallax":
        return "subtle parallax drift"
    if animation_type == "diagram drawing animation":
        return "line-by-line reveal"
    if animation_type == "infographic animation":
        return "icon and chart reveal"
    return "slow zoom in"


def _truncate_to_two_sentences(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(parts) <= 2:
        return " ".join(parts)
    return " ".join(parts[:2])


def _fallback_scene(idx: int) -> Dict[str, Any]:
    title = f"Concept {idx + 1}"
    return {
        "scene_id": idx + 1,
        "title": title,
        "narration_script": "This scene explains a key concept from the research content.",
        "visual_description": f"Flat infographic visual explaining {title.lower()}.",
        "visual_prompt": f"Educational infographic, flat design, 16:9, {title.lower()}",
        "camera_shot": "medium shot",
        "animation_type": "zoom",
        "motion_direction": "slow zoom in",
        "visual_layers": ["background", "diagram", "labels"],
        "text_overlay": title,
        "transition": "fade",
        "duration": 6,
        "source_reference": "Source content",
        "confidence_score": 0.8,
    }


async def generate_video_plan_data(content: str, title: str = "Research Explainer") -> Dict[str, Any]:
    target_scenes = _adaptive_scene_count(content)
    raw_plan = await generate_video_plan(content, target_scenes)

    plan_container = raw_plan.get("video_plan", raw_plan)
    if not isinstance(plan_container, dict):
        plan_container = {}
    input_scenes = plan_container.get("scenes") if isinstance(plan_container, dict) else []
    if not isinstance(input_scenes, list):
        input_scenes = []

    normalized_scenes: List[Dict[str, Any]] = []
    if not input_scenes:
        input_scenes = [_fallback_scene(i) for i in range(target_scenes)]

    for i, scene in enumerate(input_scenes):
        if not isinstance(scene, dict):
            scene = {}
        animation_type = _normalize_animation_type(scene.get("animation_type"))
        motion_direction = str(scene.get("motion_direction") or "").strip() or _default_motion(animation_type)
        narration = _truncate_to_two_sentences(
            str(scene.get("narration_script") or scene.get("narration") or "").strip()
        )
        if not narration:
            narration = _fallback_scene(i)["narration_script"]

        normalized = {
            "scene_id": i + 1,
            "title": str(scene.get("title") or f"Scene {i + 1}").strip(),
            "narration_script": narration,
            "visual_description": str(scene.get("visual_description") or "").strip() or f"Educational visual for scene {i + 1}.",
            "visual_prompt": str(scene.get("visual_prompt") or "").strip() or f"Educational infographic, flat design, scene {i + 1}",
            "camera_shot": str(scene.get("camera_shot") or "medium shot").strip(),
            "animation_type": animation_type,
            "motion_direction": motion_direction,
            "visual_layers": _parse_layers(scene.get("visual_layers")) or ["background", "diagram", "labels"],
            "text_overlay": str(scene.get("text_overlay") or scene.get("title") or f"Scene {i + 1}").strip(),
            "transition": str(scene.get("transition") or "fade").strip(),
            "duration": _clamp_duration(scene.get("duration"), 6),
            "source_reference": str(scene.get("source_reference") or "Source content").strip(),
            "confidence_score": _clamp_confidence(scene.get("confidence_score"), 0.85),
        }
        normalized_scenes.append(normalized)

    for scene in normalized_scenes:
        try:
            check = await fact_check_scene(
                narration=scene["narration_script"],
                source_content=content,
                source_reference=scene["source_reference"],
            )
            scene["confidence_score"] = _clamp_confidence(check.get("confidence_score"), scene["confidence_score"])
            source_ref = str(check.get("source_reference") or "").strip()
            if source_ref:
                scene["source_reference"] = source_ref
        except Exception as e:
            print(f"[PlanningService] Fact-check skipped for scene {scene['scene_id']}: {e}")

    total_duration = int(sum(int(scene["duration"]) for scene in normalized_scenes))
    normalized_plan = {
        "video_plan": {
            "title": str(plan_container.get("title") or title or "Research Explainer").strip(),
            "total_scenes": len(normalized_scenes),
            "estimated_video_duration": f"{total_duration} seconds",
            "visual_style": str(plan_container.get("visual_style") or DEFAULT_VISUAL_STYLE).strip(),
            "scenes": normalized_scenes,
        }
    }
    return normalized_plan


def _scene_payload_for_storyboard(scenes: List[Scene]) -> Dict[str, Any]:
    return {
        "scenes": [
            {
                "scene_id": i + 1,
                "title": s.scene_title,
                "narration_script": s.script,
                "visual_prompt": s.visual_prompt,
            }
            for i, s in enumerate(scenes)
        ]
    }


def _as_layer_json(value: Any) -> str:
    layers = _parse_layers(value)
    return json.dumps(layers)


async def refine_scenes_with_storyboard(db: AsyncSession, project_id: int) -> None:
    """
    Optional non-blocking storyboard refinement.
    Keeps planning values when storyboard output is incomplete.
    """
    scenes = await get_scenes(db, project_id)
    if not scenes:
        return

    payload = _scene_payload_for_storyboard(scenes)

    try:
        storyboard = await generate_storyboard(json.dumps(payload))
        items = storyboard.get("storyboard", [])
        if not isinstance(items, list) or not items:
            return

        for i, item in enumerate(items):
            if not isinstance(item, dict) or i >= len(scenes):
                continue
            scene = scenes[i]

            visual_description = str(item.get("visual_description") or "").strip()
            if visual_description:
                scene.visual_description = visual_description

            camera_shot = str(item.get("camera_shot") or "").strip()
            if camera_shot:
                scene.camera_shot = camera_shot

            animation = item.get("animation_type") or item.get("animation_style")
            animation_type = _normalize_animation_type(animation)
            if animation_type:
                scene.animation_type = animation_type

            motion_direction = str(item.get("motion_direction") or "").strip()
            if motion_direction:
                scene.motion_direction = motion_direction

            visual_layers = item.get("visual_layers")
            if visual_layers is not None:
                scene.visual_layers = _as_layer_json(visual_layers)

            text_overlay = str(item.get("text_overlay") or "").strip()
            if text_overlay:
                scene.text_overlay = text_overlay

            transition = str(item.get("transition") or "").strip()
            if transition:
                scene.transition = transition

        await db.commit()
    except Exception as e:
        print(f"[PlanningService] Storyboard refinement skipped: {e}")
