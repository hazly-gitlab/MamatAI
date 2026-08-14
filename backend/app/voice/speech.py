import os
from io import BytesIO
from typing import Optional
from gtts import gTTS
from backend.app.core.config import settings

def transcribe_audio(file_path: str, language: str = "en") -> str:
    """
    Transcribe audio file path into text.
    If STT_PROVIDER is mock, returns a realistic placeholder text or simulates based on context.
    If STT_PROVIDER is openai, can utilize cloud APIs.
    """
    if settings.STT_PROVIDER.lower() == "openai":
        # Cloud API integration can go here
        pass

    # Return mock/test transcription
    # For a real voice experience, we support a simple query
    return "Hello JARVIS, tell me a joke and calculate 10 times 5."

def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Synthesize text into speech audio bytes (MP3 format).
    Uses lightweight gTTS (Google Text-to-Speech) library which runs on CPU on host.
    """
    try:
        # Map languages
        # English: 'en', Malay: 'ms'
        lang_code = "en"
        if language.lower() in ["ms", "mly", "malay", "ms-my"]:
            lang_code = "ms"

        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        # Fallback empty sound
        return b""
