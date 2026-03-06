import json
from fastapi import WebSocket
from agents.edit_agent import agentic_edit_scene
from services.scene_service import get_scene, update_scene
from services.video_service import regenerate_single_scene
from database.db import async_session

class ConnectionManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def send(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            print(f"WebSocket send error: {e}")

manager = ConnectionManager()

async def handle_scene_edit(websocket: WebSocket, data: dict):
    scene_data = data.get("scene", {})
    scene_id = scene_data.get("id") or scene_data.get("scene_id")
    instruction = data.get("instruction", "")

    if not scene_id or not instruction:
        return

    async with async_session() as db:
        scene = await get_scene(db, scene_id)
        if not scene:
            return

        # Notify UI about AI processing
        await manager.send(websocket, {
            "type": "status",
            "message": "AI is analyzing your edit instruction...",
            "scene_id": scene_id
        })

        current_scene_dict = {
            "title": scene.scene_title,
            "narration_script": scene.script,
            "visual_prompt": scene.visual_prompt,
            "voice_tone": scene.voice_tone,
            "duration": scene.duration,
        }

        updated_json = await agentic_edit_scene(
            current_scene_json=json.dumps(current_scene_dict),
            user_instruction=instruction,
        )

        updates = {}
        if "title" in updated_json: updates["scene_title"] = updated_json["title"]
        if "narration_script" in updated_json: updates["script"] = updated_json["narration_script"]
        if "visual_prompt" in updated_json: updates["visual_prompt"] = updated_json["visual_prompt"]
        if "voice_tone" in updated_json: updates["voice_tone"] = updated_json["voice_tone"]
        if "duration" in updated_json:
            try:
                updates["duration"] = float(updated_json["duration"])
            except (ValueError, TypeError):
                pass

        await update_scene(db, scene_id, updates)

        await manager.send(websocket, {
            "type": "status",
            "message": "Generating visually enhanced video clip...",
            "scene_id": scene_id
        })

        # Regenerate media logic
        await regenerate_single_scene(db, scene_id)

        # Get the thoroughly regenerated scene
        final_scene = await get_scene(db, scene_id)
        
        scene_dict = {
            "id": final_scene.id,
            "scene_index": final_scene.scene_index,
            "scene_title": final_scene.scene_title,
            "script": final_scene.script,
            "visual_prompt": final_scene.visual_prompt,
            "image_url": final_scene.image_url,
            "audio_url": final_scene.audio_url,
            "video_clip": final_scene.video_clip,
            "source_reference": final_scene.source_reference,
            "confidence_score": final_scene.confidence_score,
            "version": final_scene.version,
            "duration": final_scene.duration,
            "voice_tone": final_scene.voice_tone,
            "status": final_scene.status,
        }

        await manager.send(websocket, {
            "type": "scene_updated",
            "scene": scene_dict
        })
