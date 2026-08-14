import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.voice.speech import synthesize_speech, transcribe_audio
from app.vision.vision import analyze_image_file

def test_speech_synthesis():
    audio_bytes = synthesize_speech("Hello, this is a test.", "en")
    assert audio_bytes is not None
    assert len(audio_bytes) > 0

    malay_bytes = synthesize_speech("Apa khabar?", "ms")
    assert len(malay_bytes) > 0

def test_vision_descriptions():
    desc_err = analyze_image_file("screenshot_error.png", "Explain this error")
    assert "ConnectionRefusedError" in desc_err

    desc_diag = analyze_image_file("architecture.png", "Analyze this architecture diagram")
    assert "Nginx Reverse Proxy" in desc_diag or "FastAPI" in desc_diag

    desc_desc = analyze_image_file("random.png", "What is shown in this image?")
    assert "vision" in desc_desc.lower() or "interface" in desc_desc.lower()
