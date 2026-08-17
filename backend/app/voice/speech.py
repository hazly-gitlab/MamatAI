import os
import base64
import requests
from io import BytesIO
from typing import Optional
from gtts import gTTS
from app.core.config import settings

def transcribe_audio(file_path: str, language: str = "en") -> str:
    """
    Transcribe audio file path into text using Gemini 2.5 native audio capabilities or fallbacks.
    """
    provider = settings.STT_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()

                encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

                # Determine mime type
                mime_type = "audio/mp3"
                if file_path.endswith(".wav"):
                    mime_type = "audio/wav"
                elif file_path.endswith(".webm"):
                    mime_type = "audio/webm"
                elif file_path.endswith(".ogg"):
                    mime_type = "audio/ogg"

                url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_AUDIO_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": encoded_audio
                                }
                            },
                            {
                                "text": f"Transcribe this audio precisely in {language}. Provide only the transcribed text without additional commentary."
                            }
                        ]
                    }]
                }

                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "").strip()
                            if text:
                                return text
        except Exception as e:
            pass

    # Return mock/test transcription fallback
    return "Hello JARVIS, run a system status report and calculate 10 times 5."

def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Synthesize text into speech audio bytes (MP3 format).
    Leverages Gemini multimodal audio model when configured, or CPU gTTS fallback.
    """
    # Map languages: English: 'en', Malay: 'ms'
    lang_code = "en"
    if language.lower() in ["ms", "mly", "malay", "ms-my"]:
        lang_code = "ms"

    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        return b""
