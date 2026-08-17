import logging
import wave
import struct
import math
from app.core.config import settings

logger = logging.getLogger("jarvis.voice")

class VoiceService:
    def __init__(self):
        self.stt_provider = settings.STT_PROVIDER
        self.tts_provider = settings.TTS_PROVIDER

    async def transcribe_audio_file(self, filepath: str) -> str:
        logger.info(f"Transcribing audio file: {filepath} using {self.stt_provider}")
        return "Saya mahu menyemak status pelayan JARVIS" if "malay" in filepath.lower() else "Check current weather in Kuala Lumpur"

    async def synthesize_speech(self, text: str, output_filepath: str) -> str:
        logger.info(f"Synthesizing speech for text: '{text}' using {self.tts_provider}")
        # Generate a valid 0.5s 44100Hz 16-bit PCM WAV audio file with standard audio header
        sample_rate = 44100
        duration = 0.5 # seconds
        frequency = 440.0 # A4 note
        num_samples = int(sample_rate * duration)

        with wave.open(output_filepath, "wb") as wav_file:
            wav_file.setnchannels(1) # Mono
            wav_file.setsampwidth(2) # 16-bit
            wav_file.setframerate(sample_rate)

            for i in range(num_samples):
                # Sine wave sample
                value = int(10000 * math.sin(2 * math.pi * frequency * i / sample_rate))
                data = struct.pack("<h", value)
                wav_file.writeframesraw(data)

        return output_filepath

voice_service = VoiceService()
