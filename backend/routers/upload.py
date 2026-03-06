"""
Upload Router: Handles file upload and text content submission.
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Project
from services.script_service import extract_text_from_file
from config import settings

router = APIRouter()


@router.post("/upload_content")
async def upload_content(
    file: UploadFile = File(None),
    text_content: str = Form(None),
    title: str = Form("Untitled Project"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file (PDF/DOCX/TXT) or paste text content."""
    content = ""

    if file:
        # Save uploaded file
        ext = os.path.splitext(file.filename)[1] if file.filename else ".txt"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)

        file_bytes = await file.read()
        with open(filepath, "wb") as f:
            f.write(file_bytes)

        # Extract text
        content = await extract_text_from_file(filepath, file.content_type or "")

        if not title or title == "Untitled Project":
            title = file.filename or "Untitled Project"

    elif text_content:
        content = text_content
    else:
        raise HTTPException(status_code=400, detail="No file or text content provided")

    if not content.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded content")

    # Create project
    project = Project(
        title=title,
        original_content=content,
        status="created",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {
        "project_id": project.id,
        "title": project.title,
        "content_length": len(content),
        "status": project.status,
        "content_preview": content[:500],
    }
