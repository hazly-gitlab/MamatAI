import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.security.auth import require_write_user
from app.voice.voice_service import voice_service
from app.vision.vision_service import vision_service
from app.core.config import settings

router = APIRouter(tags=["Voice & Vision API"])

@router.post("/voice/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    user=Depends(require_write_user)
):
    temp_filename = f"stt_temp_{uuid.uuid4()}_{file.filename}"
    temp_filepath = os.path.join(settings.UPLOAD_DIR, temp_filename)
    try:
        with open(temp_filepath, "wb") as f:
            f.write(await file.read())

        transcript = await voice_service.transcribe_audio_file(temp_filepath)
        return {"transcript": transcript}
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


@router.post("/voice/tts")
async def text_to_speech(
    text: str = Form(...),
    user=Depends(require_write_user)
):
    output_filename = f"tts_output_{uuid.uuid4()}.wav"
    output_filepath = os.path.join(settings.UPLOAD_DIR, output_filename)

    await voice_service.synthesize_speech(text, output_filepath)
    return FileResponse(output_filepath, media_type="audio/wav", filename="reply.wav")


@router.post("/vision/analyse")
async def vision_analyse(
    file: UploadFile = File(...),
    query: str = Form("Describe this image"),
    user=Depends(require_write_user)
):
    filename = f"vision_temp_{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(await file.read())

        analysis = await vision_service.analyze_image(filepath, query)
        return {"analysis": analysis}
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
