import os
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import mss
import httpx
from PIL import Image
from backend.config import settings

logger = logging.getLogger("AEGIS.Screen")

class ScreenVisionService:
    def capture_screen_base64(self) -> Optional[str]:
        try:
            temp_path = Path(settings.BASE_DIR) / "data" / "screen_temp.jpg"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            with mss.mss() as sct:
                sct.shot(mon=-1, output=str(temp_path))
            
            # Compress and resize if large for vision API efficiency
            with Image.open(temp_path) as img:
                img.thumbnail((1280, 720))
                img.save(temp_path, "JPEG", quality=75)

            with open(temp_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    async def analyze_screen_content(self, user_question: str) -> Dict[str, Any]:
        """Analyzes active screen content and answers user question (e.g. read error, find button)."""
        screen_b64 = self.capture_screen_base64()
        if not screen_b64:
            return {"status": "error", "message": "Failed to capture the screen."}

        if not settings.OPENROUTER_API_KEY:
            return {
                "status": "offline",
                "message": "Screen capture is ready, but an AI vision key is required for deep analysis."
            }

        prompt = (
            f"The user is asking about what is on their Windows computer screen:\n"
            f"User Question: '{user_question}'\n\n"
            f"Inspect the provided screen capture and answer concisely, clearly reading any error messages, "
            f"identifying relevant active windows, or pointing out buttons/text."
        )

        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aegis-assistant.ai",
                "X-Title": "AEGIS Assistant"
            }
            payload = {
                "model": settings.VISION_MODEL or settings.OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screen_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.3
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )

            if resp.status_code == 200:
                result = resp.json()
                answer = result["choices"][0]["message"]["content"]
                return {
                    "status": "success",
                    "analysis": answer,
                    "message": answer
                }
            else:
                return {"status": "api_error", "message": "Unable to analyze the screen image with cloud vision."}
        except Exception as e:
            return {"status": "error", "message": f"Screen analysis error: {str(e)}"}

screen_vision_service = ScreenVisionService()
