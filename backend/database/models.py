import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=False)
    original_content = Column(Text, nullable=True)
    status = Column(String(50), default="created")  # created, scripted, generating, completed
    final_video_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="projects")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan",
                          order_by="Scene.scene_index")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    scene_index = Column(Integer, nullable=False)
    scene_title = Column(String(500), nullable=False)
    script = Column(Text, nullable=True)
    visual_prompt = Column(Text, nullable=True)
    image_url = Column(String(1000), nullable=True)
    audio_url = Column(String(1000), nullable=True)
    video_clip = Column(String(1000), nullable=True)
    source_reference = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    version = Column(Integer, default=1)
    duration = Column(Float, default=5.0)
    voice_tone = Column(String(100), default="neutral")
    status = Column(String(50), default="pending")  # pending, generating, completed, error
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="scenes")


class SceneVersion(Base):
    __tablename__ = "scene_versions"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    version = Column(Integer, nullable=False)
    script = Column(Text, nullable=True)
    visual_prompt = Column(Text, nullable=True)
    image_url = Column(String(1000), nullable=True)
    audio_url = Column(String(1000), nullable=True)
    video_clip = Column(String(1000), nullable=True)
    source_reference = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scene = relationship("Scene")
