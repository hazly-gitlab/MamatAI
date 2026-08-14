from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
import tempfile
import os
from typing import Optional

from app.api.deps import get_current_active_user
from app.models.models import User
from app.vision.vision import analyze_image_file

router = APIRouter()

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    query: Optional[str] = Form(None),
    user: User = Depends(get_current_active_user)
):
    """Upload an image (screenshot, diagram, table) and perform layout/OCR/object analysis."""
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format. Allowed formats: PNG, JPG, JPEG, WEBP, BMP"
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_name = tmp.name

    try:
        description = analyze_image_file(tmp_name, query)
        return {
            "status": "success",
            "filename": file.filename,
            "analysis": description
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image vision analysis failed: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
