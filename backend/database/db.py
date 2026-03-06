from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from database.models import User, Project, Scene, SceneVersion  # noqa
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_additive_columns)


def _ensure_additive_columns(sync_conn):
    """
    Lightweight additive migration to keep existing local DBs compatible.
    """
    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())

    if "scenes" in tables:
        scene_cols = {c["name"] for c in inspector.get_columns("scenes")}
        scene_additions = {
            "visual_description": "TEXT",
            "camera_shot": "VARCHAR(120)",
            "animation_type": "VARCHAR(120)",
            "motion_direction": "VARCHAR(120)",
            "visual_layers": "TEXT",
            "text_overlay": "VARCHAR(500)",
            "transition": "VARCHAR(120)",
        }
        for name, ddl in scene_additions.items():
            if name not in scene_cols:
                sync_conn.execute(text(f"ALTER TABLE scenes ADD COLUMN {name} {ddl}"))

    if "scene_versions" in tables:
        version_cols = {c["name"] for c in inspector.get_columns("scene_versions")}
        version_additions = {
            "visual_description": "TEXT",
            "camera_shot": "VARCHAR(120)",
            "animation_type": "VARCHAR(120)",
            "motion_direction": "VARCHAR(120)",
            "visual_layers": "TEXT",
            "text_overlay": "VARCHAR(500)",
            "transition": "VARCHAR(120)",
        }
        for name, ddl in version_additions.items():
            if name not in version_cols:
                sync_conn.execute(text(f"ALTER TABLE scene_versions ADD COLUMN {name} {ddl}"))
