import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App
    APP_NAME: str = "StoryHack Agentic Editor"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database (SQLite for local dev, switch to PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./storyhack.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "alloy"

    # Stability AI (Stable Diffusion)
    STABILITY_API_KEY: str = ""
    STABILITY_API_URL: str = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

    # ElevenLabs (optional)
    ELEVENLABS_API_KEY: str = ""

    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    MEDIA_DIR: str = "storage/media"
    VIDEO_DIR: str = "storage/videos"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Create storage directories
for d in [settings.UPLOAD_DIR, settings.MEDIA_DIR, settings.VIDEO_DIR]:
    os.makedirs(d, exist_ok=True)
