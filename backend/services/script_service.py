"""
Script Service: Orchestrates document parsing and script generation pipeline.
"""
import os
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from agents.script_agent import generate_script
from agents.factcheck_agent import fact_check_scene


async def extract_text_from_file(filepath: str, content_type: str) -> str:
    """Extract text from uploaded file based on content type."""
    if content_type == "application/pdf" or filepath.endswith(".pdf"):
        return _extract_pdf(filepath)
    elif content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ] or filepath.endswith(".docx"):
        return _extract_docx(filepath)
    else:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def _extract_pdf(filepath: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


def _extract_docx(filepath: str) -> str:
    """Extract text from a DOCX file."""
    doc = DocxDocument(filepath)
    return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])


async def generate_video_script(content: str) -> dict:
    """Full pipeline: content → script → fact-check."""
    # Step 1: Generate script via Script Agent
    script_data = await generate_script(content)

    # Step 2: Fact-check each scene
    if "scenes" in script_data:
        for scene in script_data["scenes"]:
            check_result = await fact_check_scene(
                narration=scene.get("narration", ""),
                source_content=content,
                source_reference=scene.get("source_reference", ""),
            )
            scene["confidence"] = check_result.get("confidence_score", scene.get("confidence", 0.8))
            scene["source_reference"] = check_result.get("source_reference", scene.get("source_reference", ""))
            scene["fact_check"] = {
                "is_faithful": check_result.get("is_faithful", True),
                "reasoning": check_result.get("reasoning", ""),
            }

    return script_data
