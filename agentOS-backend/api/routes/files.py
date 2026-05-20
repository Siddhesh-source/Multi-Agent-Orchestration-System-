"""
File API Routes
===============

Serve generated files (PDF, PPTX, DOCX) for download.
"""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])

OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


class FileInfo(BaseModel):
    filename: str
    size: int
    created_at: str
    download_url: str


@router.get("/")
async def list_files():
    """List all generated files."""
    files = []
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file():
            stat = f.stat()
            files.append({
                "filename": f.name,
                "size": stat.st_size,
                "created_at": stat.st_ctime,
                "download_url": f"/api/files/{f.name}",
            })
    return {"files": files, "count": len(files)}


@router.get("/{filename}")
async def download_file(filename: str):
    """Download a generated file."""
    # Security: prevent path traversal
    safe_name = os.path.basename(filename)
    filepath = OUTPUT_DIR / safe_name
    
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}"
        )
    
    # Determine media type
    media_type = None
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.endswith(".html"):
        media_type = "text/html"
    
    return FileResponse(
        filepath,
        media_type=media_type,
        filename=filename,
    )


@router.delete("/{filename}")
async def delete_file(filename: str):
    """Delete a generated file."""
    safe_name = os.path.basename(filename)
    filepath = OUTPUT_DIR / safe_name
    
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found"
        )
    
    filepath.unlink()
    return {"success": True, "deleted": filename}
