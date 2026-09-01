import os
import re
import json
import base64
import logging
import numpy as np
import cv2
from typing import List, Dict, Any, Optional
from PIL import Image
from backend.config import settings

logger = logging.getLogger("AEGIS.LocateAnything")

class LocateAnythingDetector:
    """
    NVIDIA LocateAnything-3B Vision-Language Grounding Detector.
    Uses HuggingFace transformers pipeline:
      pipe = pipeline("image-text-to-text", model="nvidia/LocateAnything-3B", trust_remote_code=True)
    """

    def __init__(self):
        self.model_id = getattr(settings, "NVIDIA_MODEL_ID", "nvidia/LocateAnything-3B")
        self.pipe = None
        self._is_loading = False
        self._load_failed = False

    def load_pipeline(self):
        """Initializes the HuggingFace transformers image-text-to-text pipeline for LocateAnything-3B."""
        if self.pipe is not None or self._is_loading or self._load_failed:
            return self.pipe

        self._is_loading = True
        try:
            from transformers import pipeline
            import torch

            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Loading LocateAnything-3B pipeline with device={device}...")

            self.pipe = pipeline(
                "image-text-to-text",
                model=self.model_id,
                trust_remote_code=True,
                device=device
            )
            logger.info(f"NVIDIA LocateAnything-3B pipeline loaded successfully on {'GPU' if device >= 0 else 'CPU'}")
            return self.pipe
        except Exception as e:
            self._load_failed = True
            logger.warning(f"Could not load LocateAnything-3B transformer pipeline ({e}). Will use local fallback detector.")
            return None
        finally:
            self._is_loading = False

    def detect_objects(self, img_cv: np.ndarray, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Runs visual grounding using the LocateAnything-3B pipeline.
        
        Usage example:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_img},
                        {"type": "text", "text": "Locate all objects..."}
                    ]
                }
            ]
            pipe(text=messages)
        """
        if img_cv is None or img_cv.size == 0:
            return []

        h_orig, w_orig = img_cv.shape[:2]

        # Ensure pipeline is loaded
        pipe = self.load_pipeline()
        if pipe is None:
            return []

        try:
            # Convert OpenCV BGR to PIL Image
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)

            prompt_text = (
                f"Locate the {query} with bounding boxes in format [ymin, xmin, ymax, xmax]."
                if query else
                "Detect and locate all everyday objects in this image (person, phone, bottle, mug, laptop, remote, keyboard, mouse, painting, pillow, chair, bed, desk, book) with bounding boxes in format [ymin, xmin, ymax, xmax]."
            )

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_image},
                        {"type": "text", "text": prompt_text}
                    ]
                }
            ]

            raw_outputs = pipe(text=messages, max_new_tokens=256)
            
            # Extract generated text from pipeline output
            generated_text = ""
            if isinstance(raw_outputs, list) and len(raw_outputs) > 0:
                item = raw_outputs[0]
                if isinstance(item, dict):
                    generated_text = item.get("generated_text", str(item))
                else:
                    generated_text = str(item)
            elif isinstance(raw_outputs, str):
                generated_text = raw_outputs

            return self.parse_locateanything_output(generated_text, w_orig, h_orig)

        except Exception as e:
            logger.error(f"Error during LocateAnything-3B inference: {e}")
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
            if not label or len(label) < 2 or label in ("box", "coordinates", "text"):
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

locate_anything_detector = LocateAnythingDetector()
