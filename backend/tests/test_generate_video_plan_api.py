import asyncio

from fastapi.testclient import TestClient

from database.db import async_session, init_db
from database.models import Project
from main import app
import routers.script as script_router


async def _create_project() -> int:
    async with async_session() as db:
        project = Project(
            title="API Test Project",
            original_content="This is a research paragraph about machine learning models and evaluation.",
            status="created",
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project.id


def test_generate_video_plan_endpoint_shape(monkeypatch):
    async def fake_plan(content: str, title: str):
        return {
            "video_plan": {
                "title": title,
                "total_scenes": 1,
                "estimated_video_duration": "6 seconds",
                "visual_style": "educational infographic",
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Intro",
                        "narration_script": "A concise explanation.",
                        "visual_description": "Diagram with labels.",
                        "visual_prompt": "flat educational infographic",
                        "camera_shot": "wide shot",
                        "animation_type": "zoom",
                        "motion_direction": "slow zoom in",
                        "visual_layers": ["background", "diagram", "labels"],
                        "text_overlay": "Intro",
                        "transition": "fade",
                        "duration": 6,
                        "source_reference": "Abstract",
                        "confidence_score": 0.93,
                    }
                ],
            }
        }

    monkeypatch.setattr(script_router, "generate_video_plan_data", fake_plan)
    asyncio.run(init_db())
    project_id = asyncio.run(_create_project())

    with TestClient(app) as client:
        response = client.post("/api/generate_video_plan", json={"project_id": project_id})
        assert response.status_code == 200
        data = response.json()
        assert list(data.keys()) == ["video_plan"]
        video_plan = data["video_plan"]
        assert video_plan["total_scenes"] == 1
        assert video_plan["visual_style"] == "educational infographic"
        assert set(video_plan["scenes"][0].keys()) == {
            "scene_id",
            "title",
            "narration_script",
            "visual_description",
            "visual_prompt",
            "camera_shot",
            "animation_type",
            "motion_direction",
            "visual_layers",
            "text_overlay",
            "transition",
            "duration",
            "source_reference",
            "confidence_score",
        }
