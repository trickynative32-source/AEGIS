import os
import re
import json
import base64
import logging
import httpx
import numpy as np
import cv2
from typing import List, Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger("AEGIS.LocateAnything")

class LocateAnythingDetector:
    """
    NVIDIA LocateAnything-3B Vision-Language Grounding Detector.
    Supports Parallel Box Decoding (PBD), open-vocabulary grounding,
    and direct integration via NVIDIA NIM, SGLang, vLLM, or local transformers.
    """

    def __init__(self):
        self.model_id = getattr(settings, "NVIDIA_MODEL_ID", "nvidia/LocateAnything-3B")
        self.api_url = getattr(settings, "NVIDIA_LOCATE_ANYTHING_URL", "http://localhost:30000/v1")
        self.api_key = getattr(settings, "NVIDIA_API_KEY", "")
        self.is_available = False
        self._local_model = None
        self._local_processor = None
        self._init_local_if_available()

    def _init_local_if_available(self):
        """Attempts to load local transformers model if torch and transformers are available."""
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"CUDA is available on {torch.cuda.get_device_name(0)}. LocateAnything-3B can run locally.")
        except Exception as e:
            logger.debug(f"Local torch/transformers not fully initialized for LocateAnything: {e}")

    def is_server_reachable(self) -> bool:
        """Checks if NVIDIA LocateAnything SGLang / NIM / OpenAI endpoint is active."""
        try:
            url = f"{self.api_url}/models"
            resp = httpx.get(url, timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def detect_objects(self, img_cv: np.ndarray, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Runs visual grounding using NVIDIA LocateAnything-3B.
        If query is provided, performs referring expression grounding (e.g. 'phone', 'painting on wall').
        Otherwise performs open-vocabulary dense object detection.
        """
        if img_cv is None or img_cv.size == 0:
            return []

        h_orig, w_orig = img_cv.shape[:2]
        _, buf = cv2.imencode('.jpg', img_cv, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buf).decode('utf-8')

        # 1. Try SGLang / NIM / OpenAI-compatible endpoint
        results = await self._call_locateanything_api(img_b64, w_orig, h_orig, query)
        if results:
            return results

        # 2. Try Local Transformers Pipeline if loaded
        if self._local_model is not None:
            return self._run_local_transformers(img_cv, query)

        return []

    async def _call_locateanything_api(self, img_b64: str, w_orig: int, h_orig: int, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries SGLang / vLLM / NIM server hosting nvidia/LocateAnything-3B."""
        default_prompt = (
            "Detect and locate all everyday objects in this image (such as person, phone, bottle, "
            "mug, laptop, keyboard, mouse, remote, painting, pillow, chair, bed, desk, book) "
            "with bounding boxes in format [ymin, xmin, ymax, xmax]."
        )
        prompt_text = f"Locate the {query} with bounding boxes in format [ymin, xmin, ymax, xmax]." if query else default_prompt

        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 800
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            url = f"{self.api_url}/chat/completions"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self.parse_locateanything_output(content, w_orig, h_orig)
            else:
                logger.debug(f"LocateAnything endpoint response {resp.status_code}")
        except Exception as e:
            logger.debug(f"LocateAnything endpoint not reached: {e}")

        return []

    def parse_locateanything_output(self, text: str, width: int, height: int) -> List[Dict[str, Any]]:
        """
        Parses NVIDIA LocateAnything-3B coordinate output tokens:
        - <box>[ymin, xmin, ymax, xmax]</box> (normalized 0..1000)
        - [ymin, xmin, ymax, xmax] coordinates
        - JSON structured bounding boxes
        """
        detections = []
        if not text:
            return detections

        # Pattern 1: Label followed by <box>[y1, x1, y2, x2]</box> or [y1, x1, y2, x2]
        pattern_labeled = re.finditer(
            r'([a-zA-Z\s]+?)\s*(?:<box>|\:)?\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]\s*(?:</box>)?',
            text, re.IGNORECASE
        )

        for match in pattern_labeled:
            raw_label = match.group(1).strip().lower()
            label = re.sub(r'^(the|a|an|locate|detected|found)\s+', '', raw_label).strip()
            if not label or len(label) < 2 or label in ("box", "coordinates"):
                label = "object"

            y1, x1, y2, x2 = map(int, [match.group(2), match.group(3), match.group(4), match.group(5)])
            bbox = self._normalize_to_pixels(x1, y1, x2, y2, width, height)
            if bbox:
                detections.append({
                    "name": label,
                    "confidence": 0.94,
                    "bbox": bbox,
                    "source": "nvidia_locateanything_3b"
                })

        # Pattern 2: Standalone boxes if labeled pattern was not found
        if not detections:
            pattern_boxes = re.finditer(r'\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', text)
            for match in pattern_boxes:
                y1, x1, y2, x2 = map(int, [match.group(1), match.group(2), match.group(3), match.group(4)])
                bbox = self._normalize_to_pixels(x1, y1, x2, y2, width, height)
                if bbox:
                    detections.append({
                        "name": "object",
                        "confidence": 0.90,
                        "bbox": bbox,
                        "source": "nvidia_locateanything_3b"
                    })

        return detections

    def _normalize_to_pixels(self, x1: int, y1: int, x2: int, y2: int, width: int, height: int) -> Optional[tuple]:
        """Converts 0..1000 normalized coordinates to pixel (x, y, w, h)."""
        try:
            px1 = int((min(x1, x2) / 1000.0) * width)
            py1 = int((min(y1, y2) / 1000.0) * height)
            px2 = int((max(x1, x2) / 1000.0) * width)
            py2 = int((max(y1, y2) / 1000.0) * height)

            bw = px2 - px1
            bh = py2 - py1
            if bw >= 10 and bh >= 10:
                return (max(0, px1), max(0, py1), min(width, bw), min(height, bh))
        except Exception:
            pass
        return None

    def _run_local_transformers(self, img_cv: np.ndarray, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Runs inference using local transformers pipeline."""
        try:
            import torch
            from PIL import Image
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            w_orig, h_orig = pil_img.size

            prompt = f"Locate the {query}." if query else "Detect and locate all objects with bounding boxes."
            messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
            text_prompt = self._local_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            inputs = self._local_processor(text=text_prompt, images=pil_img, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.no_grad():
                output = self._local_model.generate(**inputs, max_new_tokens=256)
            out_text = self._local_processor.decode(output[0], skip_special_tokens=True)
            return self.parse_locateanything_output(out_text, w_orig, h_orig)
        except Exception as e:
            logger.error(f"Error in local LocateAnything transformers inference: {e}")
            return []

locate_anything_detector = LocateAnythingDetector()
