import json
import re
import logging
import datetime
import base64
import httpx
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from backend.config import settings
from backend.database import SessionLocal
from backend.models import VisualMemory
from backend.services.vision import camera_service, is_frame_covered_or_blank

logger = logging.getLogger("AEGIS.VisualMemory")

# Comprehensive object category aliases for fuzzy spatial memory search
OBJECT_ALIASES = {
    "pillow": ["pillow", "cushion", "pillows", "cushions", "bolster", "bed pillow", "throw pillow", "pillowcase"],
    "painting": ["painting", "paintings", "artwork", "art", "wall art", "canvas", "picture frame", "frame", "poster", "portrait", "wall photo", "framed photo", "photo frame", "drawing", "wall painting", "scenery"],
    "phone": ["phone", "smartphone", "mobile", "cellphone", "iphone", "android", "cell phone", "handset"],
    "remote": ["remote", "tv remote", "remote control", "clicker", "ac remote", "controller", "television remote"],
    "bottle": ["bottle", "water bottle", "flask", "tumbler", "water flask", "hydration flask", "thermos", "water jar"],
    "mug": ["mug", "coffee mug", "cup", "tea cup", "coffee cup", "tea mug", "glass"],
    "bag": ["bag", "backpack", "handbag", "schoolbag", "purse", "tote", "duffel", "satchel", "pouch"],
    "bed": ["bed", "mattress", "bedsheet", "blanket", "comforter", "duvet", "sofa", "couch"],
    "chair": ["chair", "office chair", "seat", "armchair", "stool", "swivel chair"],
    "desk": ["desk", "table", "workspace", "countertop", "bedside table", "nightstand"],
    "lamp": ["lamp", "light", "desk lamp", "table lamp", "night lamp", "ceiling light", "bulb"],
    "curtain": ["curtain", "curtains", "drapes", "blinds", "window curtain"],
    "window": ["window", "glass window", "ventilator"],
    "door": ["door", "wooden door", "room door"],
    "clock": ["clock", "wall clock", "analog clock", "digital clock", "alarm clock"],
    "watch": ["watch", "smartwatch", "wrist watch", "apple watch"],
    "glasses": ["glasses", "spectacles", "sunglasses", "eyewear", "reading glasses"],
    "headphones": ["headphones", "earphones", "headset", "airpods", "earbuds"],
    "laptop": ["laptop", "computer", "notebook", "pc", "macbook", "screen", "monitor"],
    "book": ["book", "notebook", "textbook", "diary", "journal", "novel", "papers", "files"],
    "pen": ["pen", "pencil", "marker", "stylus", "highlighter"],
    "keys": ["keys", "keychain", "car keys", "house keys", "key"],
    "wallet": ["wallet", "billfold", "purse", "cardholder", "money clip"],
    "clothes": ["clothes", "clothing", "shirt", "t-shirt", "jacket", "hoodie", "towel", "cloth"],
    "mouse": ["mouse", "computer mouse", "trackpad"],
    "keyboard": ["keyboard", "typing keyboard"]
}

class VisualMemoryEngine:
    """Manages short-term spatial environmental memory and high-accuracy multi-object/multi-human perception."""

    def store_observation(
        self,
        object_name: str,
        location_context: str,
        room: str = "current_room",
        spatial_relationship: str = "in view",
        confidence: float = 0.92,
        is_user_saved: bool = False
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            clean_name = object_name.strip().lower()
            existing = db.query(VisualMemory).filter(VisualMemory.object_name == clean_name).first()

            now = datetime.datetime.now()
            if existing:
                existing.location_context = location_context.strip()
                existing.room = room.strip()
                existing.spatial_relationship = spatial_relationship.strip()
                existing.confidence = confidence
                existing.last_seen = now
                if is_user_saved:
                    existing.is_user_saved = True
                db.commit()
                db.refresh(existing)
                return {"status": "updated", "id": existing.id, "object": existing.object_name, "updated": True}
            else:
                mem = VisualMemory(
                    object_name=clean_name,
                    location_context=location_context.strip(),
                    room=room.strip(),
                    spatial_relationship=spatial_relationship.strip(),
                    confidence=confidence,
                    last_seen=now,
                    is_user_saved=is_user_saved
                )
                db.add(mem)
                db.commit()
                db.refresh(mem)
                return {"status": "created", "id": mem.id, "object": mem.object_name, "created": True}
        except Exception as e:
            logger.error(f"Error storing visual memory: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            db.close()

    def query_object_location(self, query_text: str) -> Dict[str, Any]:
        """Resolves exact spatial queries e.g. 'Where is the pillow?', 'Where is the painting?', 'Where is my phone?'"""
        q = query_text.lower().strip()
        db = SessionLocal()
        try:
            mems = db.query(VisualMemory).order_by(VisualMemory.last_seen.desc()).all()

            # 1. Match against known aliases
            target_key = None
            for key, aliases in OBJECT_ALIASES.items():
                if any(re.search(rf"\b{re.escape(alias)}\b", q) for alias in aliases):
                    target_key = key
                    break

            for m in mems:
                obj_clean = m.object_name.lower()
                is_match = False

                if target_key and target_key in OBJECT_ALIASES:
                    is_match = any(alias in obj_clean for alias in OBJECT_ALIASES[target_key])
                else:
                    is_match = (obj_clean in q) or (len(obj_clean) > 3 and obj_clean in q)

                if is_match:
                    time_str = m.last_seen.strftime("%I:%M %p").lstrip("0")
                    rel = m.spatial_relationship.strip() if m.spatial_relationship else ""
                    loc = m.location_context.strip() if m.location_context else ""

                    if "in hand" in loc or "in hand" in rel or "held" in rel:
                        msg = f"I last saw your {m.object_name} held in your hand in front of the camera (at {time_str})."
                    elif "wall" in loc or "wall" in rel or "mounted" in rel:
                        msg = f"I saw the {m.object_name} on the {loc} in your {m.room} (last seen at {time_str})."
                    elif "bed" in loc or "pillow" in m.object_name or "cushion" in m.object_name:
                        msg = f"I last saw the {m.object_name} on the {loc} ({rel}) at {time_str}."
                    elif "beside" in loc or "beside" in rel:
                        msg = f"I last saw your {m.object_name} {loc} in your {m.room} at {time_str}."
                    elif "desk" in loc or "table" in loc:
                        if rel and rel != "in view":
                            msg = f"I last saw your {m.object_name} {rel} on the {loc} (at {time_str})."
                        else:
                            msg = f"I last saw your {m.object_name} on the {loc} at {time_str}."
                    elif "floor" in loc:
                        if rel and rel != "in view":
                            msg = f"I last saw your {m.object_name} {rel} on the {loc} at {time_str}."
                        else:
                            msg = f"I last saw your {m.object_name} on the {loc} in your {m.room} at {time_str}."
                    else:
                        msg = f"I last saw your {m.object_name} on the {loc} in your {m.room} at {time_str}."

                    return {
                        "found": True,
                        "object": m.object_name,
                        "location": m.location_context,
                        "room": m.room,
                        "spatial_relationship": m.spatial_relationship,
                        "last_seen": time_str,
                        "confidence": m.confidence,
                        "message": msg
                    }

            if "what room" in q:
                top = mems[0] if mems else None
                room_name = top.room if top else "workspace"
                return {
                    "found": True,
                    "room": room_name,
                    "message": f"It looks like you are in the {room_name}." if room_name != "workspace" else "It looks like an office or study workspace."
                }

            obj_match = re.search(r"\bwhere (?:is|did you see|are) (?:my |the )?([a-zA-Z\s]+)", q)
            queried_item = obj_match.group(1).strip().rstrip("?.!") if obj_match else "that item"

            if not camera_service.is_active:
                return {
                    "found": False,
                    "camera_off": True,
                    "message": f"The camera is currently turned off and I haven't seen your {queried_item} recently. Please turn on the camera and point it towards the room so I can locate it."
                }
            else:
                return {
                    "found": False,
                    "camera_off": False,
                    "message": f"I haven't spotted your {queried_item} in my visual memory yet. Please hold it up or point the camera at where it is kept so I can record its location."
                }
        finally:
            db.close()

    def get_all_memories(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            mems = db.query(VisualMemory).order_by(VisualMemory.last_seen.desc()).all()
            return [
                {
                    "id": m.id,
                    "object": m.object_name,
                    "location_context": m.location_context,
                    "room": m.room,
                    "spatial_relationship": m.spatial_relationship,
                    "confidence": m.confidence,
                    "last_seen": m.last_seen.strftime("%I:%M %p"),
                    "is_user_saved": m.is_user_saved
                }
                for m in mems
            ]
        finally:
            db.close()

    def clear_visual_memories(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            count = db.query(VisualMemory).filter(VisualMemory.is_user_saved == False).delete()
            db.commit()
            return {"status": "cleared", "deleted_count": count, "message": f"Cleared {count} temporary visual memories."}
        finally:
            db.close()

    async def analyze_frame_and_extract_memory(self, frame_base64: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes live camera frame with high spatial accuracy, identifying ALL everyday objects, paintings, pillows, etc."""
        if not frame_base64:
            frame_base64 = camera_service.get_latest_frame_base64()

        if not frame_base64:
            return {"status": "no_frame", "message": "No camera frame is currently available. Please ensure the camera is turned on."}

        # 1. Decode image and check for covered lens / closed physical privacy shutter
        try:
            img_bytes = base64.b64decode(frame_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            img = None

        if img is None:
            return {"status": "no_frame", "message": "Unable to decode camera frame."}

        is_covered, covered_msg = is_frame_covered_or_blank(img)
        if is_covered:
            return {
                "status": "camera_covered",
                "scene": "shutter_closed",
                "people_count": 0,
                "objects": [],
                "message": covered_msg
            }

        # 2. Try Google Gemini 2.0 Flash Vision (Direct API Key)
        if settings.GEMINI_API_KEY:
            gemini_res = await self._analyze_with_gemini_direct(frame_base64)
            if gemini_res and len(gemini_res.get("objects", [])) > 0:
                return gemini_res

        # 3. Try OpenRouter Vision (Gemini 2.0 Flash or Vision Model)
        if settings.OPENROUTER_API_KEY:
            openrouter_res = await self._analyze_with_openrouter(frame_base64)
            if openrouter_res and len(openrouter_res.get("objects", [])) > 0:
                return openrouter_res

        # 4. Deep Local Computer Vision Spatial Segmentation (Offline fallback)
        return self._analyze_with_local_cv(img)

    async def _analyze_with_gemini_direct(self, frame_base64: str) -> Optional[Dict[str, Any]]:
        """Multimodal visual perception with Gemini 2.0 Flash via google-generativeai SDK."""
        prompt = """Analyze this camera image. List ONLY objects you can ACTUALLY SEE in the image.

For each object, provide:
- name: common name (e.g. "phone", "bottle", "pillow", "painting", "remote", "laptop", "book")
- location: where it is ("in hand", "on wall", "on desk", "on bed", "on floor", "on chair", "in room")
- spatial_relationship: brief description of position

Also count visible people and identify the room type.

IMPORTANT: Only list objects you are confident are actually in the image. Do NOT guess or hallucinate objects.

Respond in JSON (no code fences):
{"scene": "room type", "people_count": 0, "people_details": [], "summary": "I see...", "objects": [{"name": "...", "location": "...", "spatial_relationship": "..."}]}"""

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")

            import io
            from PIL import Image
            img_bytes = base64.b64decode(frame_base64)
            pil_image = Image.open(io.BytesIO(img_bytes))

            response = model.generate_content(
                [prompt, pil_image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1200
                )
            )

            if response and response.text:
                logger.info(f"Gemini SDK response length: {len(response.text)}")
                return self._parse_vision_response(response.text)
        except ImportError:
            logger.warning("google-generativeai not installed, falling back to HTTP API")
            # Fallback to raw HTTP
            return await self._analyze_with_gemini_http(frame_base64)
        except Exception as e:
            logger.error(f"Gemini SDK Vision error: {e}")
        return None

    async def _analyze_with_gemini_http(self, frame_base64: str) -> Optional[Dict[str, Any]]:
        """Fallback: Gemini via raw HTTP if SDK is unavailable."""
        prompt = """Analyze this camera image. List ONLY objects you can ACTUALLY SEE. Respond in JSON:
{"scene": "room type", "people_count": 0, "summary": "I see...", "objects": [{"name": "...", "location": "...", "spatial_relationship": "..."}]}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": frame_base64}}
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1200}
        }
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_vision_response(content)
            else:
                logger.error(f"Gemini HTTP API status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Gemini HTTP Vision error: {e}")
        return None

    async def _analyze_with_openrouter(self, frame_base64: str) -> Optional[Dict[str, Any]]:
        """Analyzes frame via OpenRouter Multimodal endpoint with deep spatial reasoning."""
        prompt = """Analyze this camera image. List ONLY objects you can ACTUALLY SEE in the image.

For each object, provide:
- name: common name (e.g. "phone", "bottle", "pillow", "painting", "remote", "laptop", "book", "bag", "keys")
- location: where it is ("in hand", "on wall", "on desk", "on bed", "on floor", "on chair", "in room")
- spatial_relationship: brief description of position

Also count visible people and identify the room type.

IMPORTANT: Only list objects you are confident are actually in the image. Do NOT guess or hallucinate objects.

Respond in JSON:
{"scene": "room type", "people_count": 0, "people_details": [], "summary": "I see...", "objects": [{"name": "...", "location": "...", "spatial_relationship": "..."}]}"""

        model = settings.VISION_MODEL or "google/gemini-2.0-flash-001"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1200
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://aegis-assistant.ai"
        }
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_vision_response(content)
            else:
                logger.error(f"OpenRouter Vision status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"OpenRouter Vision error: {e}")
        return None

    def _parse_vision_response(self, text: str) -> Dict[str, Any]:
        """Parses model response, stores detected objects in visual memory. Robust against varied JSON formats."""
        summary = ""
        scene = "workspace"
        objects_stored = []
        people_count = 0

        data = None

        # Strategy 1: JSON inside ```json ... ``` code fence
        json_match = re.search(r"```(?:json)?\s*(\{.+?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 2: Raw JSON (no code fence) — find first { to last }
        if data is None:
            brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if brace_match:
                try:
                    data = json.loads(brace_match.group(1))
                except json.JSONDecodeError:
                    pass

        # Strategy 3: Try to fix common JSON issues (trailing commas)
        if data is None and "{" in text:
            cleaned = text[text.index("{"):text.rindex("}") + 1]
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # Remove trailing commas
            try:
                data = json.loads(cleaned)
            except (json.JSONDecodeError, ValueError):
                pass

        if data and isinstance(data, dict):
            summary = data.get("summary", "")
            scene = data.get("scene", "workspace")
            people_count = data.get("people_count", 0)

            for i, p_desc in enumerate(data.get("people_details", [])):
                p_name = f"person {i+1}" if people_count > 1 else "person"
                self.store_observation(
                    object_name=p_name, location_context="in front of camera",
                    room=scene, spatial_relationship=p_desc, confidence=0.96
                )
                objects_stored.append(p_name)

            for obj in data.get("objects", []):
                name = obj.get("name", "").strip().lower()
                loc = obj.get("location", "in room").strip()
                rel = obj.get("spatial_relationship", "in view").strip()
                if name and len(name) > 1:
                    self.store_observation(
                        object_name=name, location_context=loc,
                        room=scene, spatial_relationship=rel, confidence=0.95
                    )
                    if name not in objects_stored:
                        objects_stored.append(name)

            logger.info(f"Gemini Vision detected {len(objects_stored)} objects: {objects_stored}")
        else:
            logger.warning(f"Could not parse vision JSON from response: {text[:200]}")

        if not summary:
            summary = re.sub(r"```.*?```", "", text, flags=re.DOTALL).strip()
            summary = summary.split("\n")[0]

        return {
            "status": "success",
            "scene": scene,
            "people_count": people_count,
            "objects": objects_stored,
            "message": summary or f"I see {len(objects_stored)} objects in your {scene}."
        }

    def _analyze_with_local_cv(self, img: np.ndarray) -> Dict[str, Any]:
        """Local object detection using YOLOX neural network + heuristic fallback with spatial placement."""
        from backend.services.neural_detector import neural_detector

        # 1. Multi-Person Detection
        person_res = camera_service.detect_person_local()
        person_count = person_res.get("count", 0)
        people_list = person_res.get("people", [])

        # 2. Run Neural Object Detector (YOLOX + heuristic fallback)
        neural_items = neural_detector.detect(img)

        # 3. Store people in visual memory
        stored_items = []
        if person_count == 1:
            self.store_observation("person", "center of camera frame", room="workspace",
                                  spatial_relationship="in front of camera", confidence=0.94)
            stored_items.append("person")
        elif person_count > 1:
            for i, p in enumerate(people_list):
                p_label = f"person {i+1}"
                self.store_observation(p_label, p.get("position", "in view"), room="workspace",
                                      spatial_relationship=f"standing/sitting {p.get('position', '')}",
                                      confidence=0.95)
                stored_items.append(p_label)

        # 4. Store all detected objects in visual memory
        for item in neural_items:
            name = item["name"]
            if name != "person":
                self.store_observation(
                    object_name=name,
                    location_context=item["location"],
                    room="workspace",
                    spatial_relationship=item["spatial_relationship"],
                    confidence=item.get("confidence", 0.85)
                )
                if name not in stored_items:
                    stored_items.append(name)

        # 5. Build natural language summary
        obj_names = [item["name"] for item in neural_items if item["name"] != "person"]
        if obj_names:
            phrases = []
            for item in neural_items:
                if item["name"] != "person":
                    phrases.append(f"a {item['name']} {item['spatial_relationship']}")
            msg = f"I see {', '.join(phrases[:5])}."
        elif person_count > 0:
            p_text = f"{person_count} people" if person_count > 1 else "1 person"
            msg = f"I see {p_text} in front of the camera."
        else:
            msg = "I see your room but couldn't identify specific objects. Try pointing the camera more directly at items, or set up a Gemini API key for much better detection."

        status = "neural_cv" if any(item.get("source") == "yolox" for item in neural_items) else "local_cv"

        return {
            "status": status,
            "scene": "workspace",
            "people_count": person_count,
            "objects": stored_items,
            "message": msg
        }

visual_memory_engine = VisualMemoryEngine()

