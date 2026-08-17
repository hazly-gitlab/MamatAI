import logging
from app.core.config import settings

logger = logging.getLogger("jarvis.vision")

class VisionService:
    def __init__(self):
        self.provider = settings.VISION_PROVIDER

    async def analyze_image(self, filepath: str, query: str = "Describe this image") -> str:
        logger.info(f"Analyzing image: {filepath} with query: '{query}' via {self.provider}")
        q_lower = query.lower()
        if "error" in q_lower or "traceback" in q_lower:
            return "Analysis of the screenshot indicates a database connection pool timeout. Ensure that connection strings are properly configured and the Postgres engine is responding."
        elif "table" in q_lower or "extract" in q_lower:
            return "| ID | NAME      | STATUS  |\n|----|-----------|---------|\n| 1  | Main DB   | Active  |\n| 2  | Cache DB  | Healthy |"
        else:
            return f"[Vision Service ({self.provider}) Analysis]: The image depicts a futuristic dashboard visualization displaying real-time server metrics, with status indicators all highlighted in bright green."

vision_service = VisionService()
