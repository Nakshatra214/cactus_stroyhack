import asyncio

from services import planning_service


def test_adaptive_scene_count_bounds():
    short_content = "word " * 80
    medium_content = "word " * 1200
    long_content = "word " * 5000

    assert planning_service._adaptive_scene_count(short_content) == 4
    assert 4 <= planning_service._adaptive_scene_count(medium_content) <= 14
    assert planning_service._adaptive_scene_count(long_content) == 14


def test_generate_video_plan_data_normalizes_schema(monkeypatch):
    async def fake_generate_video_plan(_content: str, _target: int):
        return {
            "video_plan": {
                "title": "Test Plan",
                "scenes": [
                    {
                        "scene_id": 7,
                        "title": "Intro",
                        "narration_script": "Sentence one. Sentence two. Sentence three.",
                        "visual_description": "A diagram appears.",
                        "visual_prompt": "diagram visual",
                        "camera_shot": "wide shot",
                        "animation_type": "pan left",
                        "motion_direction": "",
                        "visual_layers": "bg, chart, labels",
                        "text_overlay": "Intro concept",
                        "transition": "fade in",
                        "duration": 13,
                        "source_reference": "Abstract",
                        "confidence_score": 3.2,
                    }
                ],
            }
        }

    async def fake_fact_check_scene(narration: str, source_content: str, source_reference: str):
        return {
            "confidence_score": 0.92,
            "source_reference": "Section 1",
            "is_faithful": True,
        }

    monkeypatch.setattr(planning_service, "generate_video_plan", fake_generate_video_plan)
    monkeypatch.setattr(planning_service, "fact_check_scene", fake_fact_check_scene)

    result = asyncio.run(planning_service.generate_video_plan_data("source text", "My Title"))
    video_plan = result["video_plan"]
    scene = video_plan["scenes"][0]

    assert set(video_plan.keys()) == {
        "title",
        "total_scenes",
        "estimated_video_duration",
        "visual_style",
        "scenes",
    }
    assert video_plan["visual_style"] == "educational infographic"
    assert video_plan["total_scenes"] == 1
    assert video_plan["estimated_video_duration"] == "10 seconds"

    assert scene["scene_id"] == 1
    assert scene["animation_type"] == "pan_left"
    assert scene["duration"] == 10
    assert scene["confidence_score"] == 0.92
    assert scene["source_reference"] == "Section 1"
    assert scene["visual_layers"] == ["bg", "chart", "labels"]
    assert scene["narration_script"] == "Sentence one. Sentence two."
