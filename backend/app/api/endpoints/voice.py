from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO
import tempfile
import os

from backend.app.api.deps import get_current_active_user
from backend.app.models.models import User
from backend.app.voice.speech import transcribe_audio, synthesize_speech

router = APIRouter()

@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = "en",
    user: User = Depends(get_current_active_user)
):
    """Upload captured audio recording and get text transcription."""
    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_name = tmp.name

    try:
        text = transcribe_audio(tmp_name, language)
        return {"text": text, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text transcription failed: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

@router.get("/synthesize")
async def synthesize(
    text: str,
    language: str = "en",
    user: User = Depends(get_current_active_user)
):
    """Convert text to speech MP3 stream."""
    try:
        audio_bytes = synthesize_speech(text, language)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS synthesis returned empty stream.")

        return StreamingResponse(
            BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech synthesis failed: {str(e)}"
        )
