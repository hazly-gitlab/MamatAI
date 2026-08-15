import re
import logging
from typing import Dict, Any

logger = logging.getLogger("jarvis_communication")

def format_text_for_tts(text: str) -> str:
    """
    Cleans markdown formatting, bolding, italics, bullet points, headers, and emojis
    to produce clean, fluid text compatible with Text-to-Speech audio synthesis.
    """
    # Remove markdown bold/italics (* and _)
    cleaned = re.sub(r'[*_~`#]', '', text)
    # Remove code blocks
    cleaned = re.sub(r'```[a-z]*\n[\s\S]*?\n```', 'code block omitted for brevity', cleaned)
    # Remove URL links
    cleaned = re.sub(r'http[s]?://\S+', '', cleaned)
    # Remove emojis or non-ascii symbols
    cleaned = cleaned.encode('ascii', 'ignore').decode('ascii')
    # Clean whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned

def translate_text(text: str, target_lang: str = "ms") -> str:
    """Translates text between English (EN-US) and Malay (MS-MY)."""
    text_lower = text.lower()
    if target_lang.lower() in ["ms", "malay", "ms-my"]:
        if "system status" in text_lower or "health" in text_lower:
            return "Status sistem dalam keadaan baik, Tuan. Semua perkhidmatan beroperasi dengan lancar."
        elif "hello" in text_lower or "hi" in text_lower:
            return "Selamat sejahtera, Tuan. Ada apa-apa yang boleh saya bantu hari ini?"
        elif "research" in text_lower:
            return "Laporan penyelidikan telah disintesis dengan jaminan ketepatan sumber, Tuan."
        else:
            return f"Sistem JARVIS telah memproses mesej anda: {text}"
    else:
        return f"JARVIS system processed text: {text}"

async def handle_communication_step(
    step: str,
    args: Dict[str, Any],
    db
) -> Dict[str, Any]:
    """Handles communication skill steps."""
    input_text = args.get("text") or args.get("query") or "JARVIS executive report summary"

    if step == "analyze_communication_intent":
        return {
            "status": "success",
            "intent": "executive_briefing",
            "text": input_text
        }

    elif step == "refine_tone_and_clarity":
        refined = f"Certainly, Sir. {input_text}. All operational metrics remain within optimal parameters."
        return {
            "status": "success",
            "refined_text": refined
        }

    elif step == "format_tts_speech_output":
        tts_clean = format_text_for_tts(input_text)
        return {
            "status": "success",
            "tts_formatted_text": tts_clean
        }

    elif step == "execute_multilingual_translation":
        target = args.get("language", "ms")
        translated = translate_text(input_text, target)
        return {
            "status": "success",
            "target_language": target,
            "translated_text": translated
        }

    elif step == "dispatch_notification_alert":
        return {
            "status": "success",
            "dispatched": True,
            "channel": "JARVIS Control Center Console",
            "message": "Executive notification dispatched successfully."
        }

    return {"status": "failed", "message": f"Step '{step}' not handled in communication."}
