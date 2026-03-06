from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from config import settings
from database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for generated media
from config import PROJECT_ROOT
storage_dir = os.path.join(PROJECT_ROOT, "storage")
os.makedirs(storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")


# Routers
from routers import upload, script, scenes, video  # noqa

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(script.router, prefix="/api", tags=["Script"])
app.include_router(scenes.router, prefix="/api", tags=["Scenes"])
app.include_router(video.router, prefix="/api", tags=["Video"])

from fastapi import WebSocket, WebSocketDisconnect
from realtime_scene_editor import manager, handle_scene_edit

@app.websocket("/ws/edit-scene")
async def websocket_scene_editor(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "edit_scene":
                await handle_scene_edit(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
