import os
import sys
import time
import asyncio
import logging
from typing import Dict, Any
from backend.services.vision import camera_service
from backend.services.scheduler import reminder_scheduler
from backend.services.tts import tts_service

logger = logging.getLogger("AEGIS.Shutdown")

GOODBYE_PATTERNS = [
    "goodbye", "bye", "bye aura", "see you", "see you later",
    "good night", "that's all", "you can stop", "exit aura",
    "close yourself", "shut down aura", "terminate aura", "quit aura"
]

def is_goodbye_request(text: str) -> bool:
    t = text.strip().lower().rstrip(".!?,")
    # Check if phrase indicates goodbye but NOT "bye, but keep working on that"
    if "keep working" in t or "don't close" in t:
        return False
    return any(t == p or t.startswith(p + " ") or t.endswith(" " + p) for p in GOODBYE_PATTERNS)

async def perform_graceful_shutdown() -> Dict[str, Any]:
    """Executes safe self-shutdown of AEGIS without touching Windows OS."""
    logger.info("Initiating graceful self-shutdown of AEGIS...")

    # 1. Stop camera and scheduler
    camera_service.stop_camera()
    reminder_scheduler.stop()

    # 2. Farewell message
    farewell_text = "Goodbye! See you later."

    # 3. Asynchronously trigger process exit after delay to let farewell audio stream
    async def _delayed_exit():
        await asyncio.sleep(2.5)
        logger.info("Terminating AEGIS process cleanly.")
        os._exit(0)

    asyncio.create_task(_delayed_exit())

    return {
        "status": "shutting_down",
        "message": farewell_text,
        "action": "exit_app"
    }
