import os
import json
import base64
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import datetime
import secrets

from backend.config import settings
from backend.database import init_db, get_db, SessionLocal
from backend.models import (
    Reminder, Memory, Routine, VisualMemory, Conversation, UserProfile,
    MessageCreate, ReminderCreate, MemoryItem, UserProfileCreate,
    UserRegisterRequest, UserLoginRequest, GoogleLoginRequest, UserProfileUpdateRequest
)
from backend.services.auth import (
    hash_password, verify_password, generate_session_token,
    sync_user_to_memory, serialize_user_profile
)
from backend.tools.registry import registry
import backend.tools  # Register all tools

from backend.services.vision import camera_service
from backend.services.neural_detector import neural_detector
from backend.services.visual_memory import visual_memory_engine
from backend.services.screen import screen_vision_service
from backend.services.tts import tts_service
from backend.services.stt import stt_service
from backend.services.scheduler import reminder_scheduler
from backend.services.routine_learner import routine_learner
from backend.services.memory import memory_store
from backend.services.shutdown import perform_graceful_shutdown
from backend.agent.router import router
from backend.agent.llm_agent import agent

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AEGIS.Main")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, data: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send JSON to websocket: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# Hook reminder notifications to WebSocket broadcast & TTS alert
async def on_reminder_due(reminder_id: int, text: str, time_str: str):
    logger.info(f"Broadcast reminder due: {text} at {time_str}")
    alert_msg = f"Reminder: {text} at {time_str}."
    
    # Generate speech audio
    audio_b64 = await tts_service.generate_speech_audio_base64(alert_msg)

    await manager.broadcast_json({
        "type": "reminder_alert",
        "id": reminder_id,
        "text": text,
        "time": time_str,
        "message": alert_msg,
        "audio_base64": audio_b64
    })

reminder_scheduler.register_callback(on_reminder_due)

# Modern FastAPI Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AEGIS database...")
    init_db()
    logger.info("Starting background reminder scheduler...")
    reminder_scheduler.start()
    yield
    logger.info("Shutting down AEGIS services...")
    camera_service.stop_camera()
    reminder_scheduler.stop()

# FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Assisted Executive Guidance and Intelligence System Backend",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Orchestration Logic for User Messages (Optimized for Sub-Second Response)
async def process_user_query(user_text: str, is_voice: bool = False) -> Dict[str, Any]:
    clean_text = user_text.strip()
    if not clean_text:
        return {"response": "I didn't catch that.", "verified": False}

    logger.info(f"Processing query: '{clean_text}' (is_voice={is_voice})")

    # Broadcast state: THINKING immediately
    await manager.broadcast_json({"type": "state_change", "state": "THINKING", "query": clean_text})

    # Append to dictation buffer if dictation mode is active
    agent.append_dictation_text(clean_text)

    # 1. Fast deterministic local router check (<5ms)
    fast_result = await router.route_and_execute(clean_text)
    
    url = None
    booking_data = None
    media_data = None

    if fast_result:
        if "pending_reminder_task" in fast_result:
            agent.last_pending_task = fast_result["pending_reminder_task"]

        response_text = fast_result["response"]
        tool_name = fast_result.get("tool", "local_fast_route")
        verified = fast_result.get("verified", True)
        action = fast_result.get("action")
        url = fast_result.get("url")
        booking_data = fast_result.get("booking_data")
        media_data = fast_result.get("media_data")
    else:
        # 2. General Agent & Reasoning loop
        await manager.broadcast_json({"type": "state_change", "state": "EXECUTING", "query": clean_text})
        agent_result = await agent.process_message(clean_text, is_voice=is_voice)
        response_text = agent_result.get("response", "Request completed.")
        tool_name = agent_result.get("tool")
        verified = agent_result.get("verified", True)
        action = agent_result.get("action")
        url = agent_result.get("url")
        booking_data = agent_result.get("booking_data")
        media_data = agent_result.get("media_data")

    # Broadcast state: SPEAKING
    await manager.broadcast_json({"type": "state_change", "state": "SPEAKING", "response": response_text})

    # Generate TTS audio if voice mode is requested
    audio_base64 = None
    if is_voice or settings.VOICE_FIRST_MODE:
        try:
            audio_base64 = await tts_service.generate_speech_audio_base64(response_text)
        except Exception as e:
            logger.warning(f"TTS audio generation notice: {e}")

    # Broadcast final response
    result_payload = {
        "type": "agent_response",
        "user_text": clean_text,
        "response": response_text,
        "tool": tool_name,
        "verified": verified,
        "action": action,
        "url": url,
        "booking_data": booking_data,
        "media_data": media_data,
        "audio_base64": audio_base64,
        "timestamp": asyncio.get_event_loop().time()
    }
    await manager.broadcast_json(result_payload)

    # Reset state: IDLE
    await manager.broadcast_json({"type": "state_change", "state": "IDLE"})

    return result_payload

# REST API Endpoints
@app.get("/api/status")
async def get_status():
    from backend.tools.system_tools import get_system_time, get_system_date, get_system_info
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "clock": get_system_time(),
        "date": get_system_date(),
        "system_info": get_system_info(),
        "camera_active": camera_service.is_active,
        "continuous_camera": camera_service.continuous_mode,
        "model": settings.OPENROUTER_MODEL,
        "has_api_key": bool(settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY)
    }

@app.post("/api/chat")
async def chat_endpoint(payload: MessageCreate):
    result = await process_user_query(payload.text, is_voice=payload.is_voice)
    return result

@app.post("/api/barge-in")
async def barge_in_endpoint():
    tts_service.cancel()
    await manager.broadcast_json({"type": "state_change", "state": "LISTENING"})
    return {"status": "cancelled"}

@app.get("/api/camera/frame")
async def get_camera_frame():
    if not camera_service.is_active:
        return Response(status_code=404, content="Camera inactive")
    frame_bytes = camera_service.get_latest_frame_bytes()
    if not frame_bytes:
        return Response(status_code=404, content="No frame")
    return Response(content=frame_bytes, media_type="image/jpeg")

@app.post("/api/camera/toggle")
async def toggle_camera(action: str = Form("toggle")):
    if action == "start" or (action == "toggle" and not camera_service.is_active):
        res = camera_service.start_camera()
    else:
        res = camera_service.stop_camera()
    await manager.broadcast_json({
        "type": "camera_status",
        "active": camera_service.is_active,
        "continuous": camera_service.continuous_mode
    })
    return res

@app.post("/api/vision/analyze")
async def analyze_vision_endpoint(payload: Optional[Dict[str, Any]] = Body(None)):
    frame_b64 = payload.get("frame_base64") if payload else None
    if frame_b64:
        camera_service.update_frame_from_base64(frame_b64)
    res = await visual_memory_engine.analyze_frame_and_extract_memory(frame_b64)
    return res

@app.get("/api/reminders")
async def get_reminders():
    res = await registry.execute("list_reminders", {})
    return res.get("result", {})

@app.post("/api/reminders")
async def add_reminder(payload: ReminderCreate):
    res = await registry.execute("create_reminder", {"text": payload.text, "time_str": payload.time_str})
    return res.get("result", {})

@app.delete("/api/reminders/{reminder_id}")
async def remove_reminder(reminder_id: int):
    res = await registry.execute("delete_reminder", {"query": str(reminder_id)})
    return res.get("result", {})

@app.get("/api/routines")
async def get_routines():
    return {
        "routines": routine_learner.get_all_routines(),
        "suggestions": routine_learner.get_proactive_suggestions()
    }

@app.delete("/api/routines/{routine_id}")
async def delete_routine_item(routine_id: int):
    return {"success": routine_learner.delete_routine(routine_id)}

@app.delete("/api/routines")
async def clear_routines():
    return {"cleared_count": routine_learner.clear_all_routines()}

@app.get("/api/memories")
async def get_memories():
    return {"memories": memory_store.get_all_memories()}

@app.post("/api/memories")
async def save_memory(item: MemoryItem):
    return memory_store.set_memory(item.key, item.value, item.category or "preference")

@app.delete("/api/memories/{memory_id}")
async def remove_memory(memory_id: int):
    return {"success": memory_store.delete_memory(memory_id)}

@app.get("/api/visual-memories")
async def get_visual_memories():
    return {"visual_memories": visual_memory_engine.get_all_memories()}

@app.delete("/api/visual-memories")
async def clear_visual_memories():
    return visual_memory_engine.clear_visual_memories()

@app.get("/api/settings")
async def get_settings():
    return {
        "OPENROUTER_MODEL": settings.OPENROUTER_MODEL,
        "VISION_MODEL": settings.VISION_MODEL,
        "TTS_PROVIDER": settings.TTS_PROVIDER,
        "TTS_VOICE": settings.TTS_VOICE,
        "CAMERA_ENABLED": settings.CAMERA_ENABLED,
        "LOCATION_ENABLED": settings.LOCATION_ENABLED,
        "LEARNING_ENABLED": settings.LEARNING_ENABLED,
        "VOICE_FIRST_MODE": settings.VOICE_FIRST_MODE,
        "has_api_key": bool(settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY)
    }

def persist_settings_to_env(updates: Dict[str, Any]):
    env_path = os.path.join(settings.BASE_DIR, ".env")
    env_lines = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_lines[k.strip()] = v.strip()
        except Exception as e:
            logger.warning(f"Reading .env notice: {e}")

    for k, v in updates.items():
        if v is not None and k in [
            "OPENROUTER_API_KEY", "GEMINI_API_KEY", "OPENROUTER_MODEL",
            "CAMERA_ENABLED", "LEARNING_ENABLED", "LOCATION_ENABLED", "VOICE_FIRST_MODE"
        ]:
            env_lines[k] = str(v)

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in env_lines.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        logger.warning(f"Writing .env notice: {e}")

@app.post("/api/settings")
async def update_settings(data: Dict[str, Any]):
    if "OPENROUTER_API_KEY" in data:
        settings.OPENROUTER_API_KEY = data["OPENROUTER_API_KEY"]
    if "GEMINI_API_KEY" in data:
        settings.GEMINI_API_KEY = data["GEMINI_API_KEY"]
    if "OPENROUTER_MODEL" in data and data["OPENROUTER_MODEL"]:
        settings.OPENROUTER_MODEL = data["OPENROUTER_MODEL"]
    if "CAMERA_ENABLED" in data:
        settings.CAMERA_ENABLED = bool(data["CAMERA_ENABLED"])
    if "LEARNING_ENABLED" in data:
        settings.LEARNING_ENABLED = bool(data["LEARNING_ENABLED"])
    if "LOCATION_ENABLED" in data:
        settings.LOCATION_ENABLED = bool(data["LOCATION_ENABLED"])
    if "VOICE_FIRST_MODE" in data:
        settings.VOICE_FIRST_MODE = bool(data["VOICE_FIRST_MODE"])

    persist_settings_to_env(data)

    return {
        "status": "updated",
        "has_api_key": bool(settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY),
        "model": settings.OPENROUTER_MODEL
    }

@app.post("/api/stt")
async def transcribe_audio_file(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    transcription = stt_service.transcribe_audio_bytes(audio_bytes)
    return {"transcription": transcription}

@app.post("/api/tts")
async def generate_tts(text: str = Form(...)):
    audio_b64 = await tts_service.generate_speech_audio_base64(text)
    return {"audio_base64": audio_b64}

# =====================================================================
# Secure User Authentication & Comprehensive Profile Endpoints
# =====================================================================

@app.post("/api/auth/register")
async def register_user(payload: UserRegisterRequest):
    db = SessionLocal()
    try:
        clean_email = payload.email.strip().lower()
        if not clean_email or "@" not in clean_email:
            raise HTTPException(status_code=400, detail="Valid email address is required.")
        if len(payload.password) < 4:
            raise HTTPException(status_code=400, detail="Password must be at least 4 characters long.")

        existing = db.query(UserProfile).filter(UserProfile.email == clean_email).first()
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email is already registered.")

        salt, hashed_pwd = hash_password(payload.password)
        session_token = generate_session_token()
        user_id = f"usr_{secrets.token_hex(6)}"

        profile = UserProfile(
            user_id=user_id,
            name=payload.name.strip(),
            email=clean_email,
            hashed_password=hashed_pwd,
            salt=salt,
            session_token=session_token,
            auth_provider="local",
            role=payload.role or "Professional",
            phone=payload.phone,
            location=payload.location,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            bio=payload.bio,
            personal_notes=payload.personal_notes,
            preferences_json=json.dumps(payload.preferences or {}),
            last_login=datetime.datetime.utcnow()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Sync all full information to AEGIS long-term memory
        sync_user_to_memory(profile)

        return {
            "status": "success",
            "message": f"Account created successfully for {profile.name}!",
            "token": session_token,
            "user": serialize_user_profile(profile)
        }
    finally:
        db.close()

@app.post("/api/auth/login")
async def login_user(payload: UserLoginRequest):
    db = SessionLocal()
    try:
        clean_email = payload.email.strip().lower()
        profile = db.query(UserProfile).filter(UserProfile.email == clean_email).first()
        if not profile or not profile.hashed_password or not profile.salt:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not verify_password(payload.password, profile.salt, profile.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        session_token = generate_session_token()
        profile.session_token = session_token
        profile.last_login = datetime.datetime.utcnow()
        db.commit()
        db.refresh(profile)

        # Re-sync memory
        sync_user_to_memory(profile)

        return {
            "status": "success",
            "message": f"Welcome back, {profile.name}!",
            "token": session_token,
            "user": serialize_user_profile(profile)
        }
    finally:
        db.close()

@app.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest):
    db = SessionLocal()
    try:
        clean_email = payload.email.strip().lower()
        profile = db.query(UserProfile).filter(UserProfile.email == clean_email).first()
        session_token = generate_session_token()

        if not profile:
            user_id = f"usr_g_{secrets.token_hex(6)}"
            profile = UserProfile(
                user_id=user_id,
                name=payload.name.strip(),
                email=clean_email,
                avatar_url=payload.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={payload.name}",
                auth_provider="google",
                session_token=session_token,
                role=payload.role or "User",
                location=payload.location,
                emergency_contact_name=payload.emergency_contact_name,
                emergency_contact_phone=payload.emergency_contact_phone,
                personal_notes=payload.personal_notes,
                last_login=datetime.datetime.utcnow()
            )
            db.add(profile)
        else:
            profile.name = payload.name.strip()
            if payload.avatar_url:
                profile.avatar_url = payload.avatar_url
            if payload.role:
                profile.role = payload.role
            if payload.location:
                profile.location = payload.location
            if payload.emergency_contact_name:
                profile.emergency_contact_name = payload.emergency_contact_name
            if payload.emergency_contact_phone:
                profile.emergency_contact_phone = payload.emergency_contact_phone
            if payload.personal_notes:
                profile.personal_notes = payload.personal_notes
            profile.auth_provider = "google"
            profile.session_token = session_token
            profile.last_login = datetime.datetime.utcnow()

        db.commit()
        db.refresh(profile)

        # Full memory sync
        sync_user_to_memory(profile)

        return {
            "status": "success",
            "message": f"Google Authentication successful! Welcome, {profile.name}.",
            "token": session_token,
            "user": serialize_user_profile(profile)
        }
    finally:
        db.close()

@app.get("/api/auth/me")
async def get_current_user_profile(authorization: Optional[str] = Header(None)):
    db = SessionLocal()
    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1].strip()

        profile = None
        if token:
            profile = db.query(UserProfile).filter(UserProfile.session_token == token).first()

        if not profile:
            profile = db.query(UserProfile).order_by(UserProfile.last_login.desc()).first()

        return {"status": "success", "user": serialize_user_profile(profile)}
    finally:
        db.close()

@app.put("/api/auth/profile")
async def update_user_profile(payload: UserProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    db = SessionLocal()
    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1].strip()

        profile = None
        if token:
            profile = db.query(UserProfile).filter(UserProfile.session_token == token).first()
        if not profile:
            profile = db.query(UserProfile).order_by(UserProfile.last_login.desc()).first()

        if not profile:
            raise HTTPException(status_code=404, detail="No active profile found to update.")

        if payload.name is not None:
            profile.name = payload.name.strip()
        if payload.role is not None:
            profile.role = payload.role.strip()
        if payload.phone is not None:
            profile.phone = payload.phone.strip()
        if payload.location is not None:
            profile.location = payload.location.strip()
        if payload.emergency_contact_name is not None:
            profile.emergency_contact_name = payload.emergency_contact_name.strip()
        if payload.emergency_contact_phone is not None:
            profile.emergency_contact_phone = payload.emergency_contact_phone.strip()
        if payload.bio is not None:
            profile.bio = payload.bio.strip()
        if payload.personal_notes is not None:
            profile.personal_notes = payload.personal_notes.strip()
        if payload.preferences is not None:
            profile.preferences_json = json.dumps(payload.preferences)
        if payload.accessibility_settings is not None:
            profile.accessibility_settings_json = json.dumps(payload.accessibility_settings)

        db.commit()
        db.refresh(profile)

        # Re-sync memory
        sync_user_to_memory(profile)

        return {
            "status": "success",
            "message": "Profile and memory successfully updated!",
            "user": serialize_user_profile(profile)
        }
    finally:
        db.close()

@app.post("/api/auth/logout")
async def logout_user(authorization: Optional[str] = Header(None)):
    db = SessionLocal()
    try:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ")[1].strip()

        if token:
            profile = db.query(UserProfile).filter(UserProfile.session_token == token).first()
            if profile:
                profile.session_token = None
                db.commit()

        return {"status": "success", "message": "Successfully logged out."}
    finally:
        db.close()

# Backwards compatibility endpoints
@app.get("/api/user/profile")
async def get_user_profile(authorization: Optional[str] = Header(None)):
    res = await get_current_user_profile(authorization)
    return res["user"]

@app.post("/api/user/login")
async def legacy_user_login(payload: UserProfileCreate):
    res = await google_login(GoogleLoginRequest(
        name=payload.name,
        email=payload.email or f"{payload.name.lower().replace(' ', '')}@local.aegis",
        avatar_url=payload.avatar_url,
        role=payload.role,
        personal_notes=payload.personal_notes
    ))
    return {"status": "success", "message": res["message"], "profile": res["user"]}

@app.post("/api/user/logout")
async def legacy_logout():
    return {"status": "success", "message": "Logged out."}

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        from backend.tools.system_tools import get_system_time, get_system_date
        await websocket.send_json({
            "type": "init",
            "message": "Connected to AEGIS System Engine.",
            "clock": get_system_time(),
            "date": get_system_date(),
            "camera_active": camera_service.is_active,
            "suggestions": routine_learner.get_proactive_suggestions()
        })

        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
                msg_type = data.get("type", "message")

                if msg_type == "message":
                    text = data.get("text", "")
                    is_voice = data.get("is_voice", False)
                    await process_user_query(text, is_voice=is_voice)

                elif msg_type == "camera_frame_sync":
                    frame_b64 = data.get("frame_base64")
                    live_detect = data.get("live_detect", True)
                    if frame_b64:
                        camera_service.update_frame_from_base64(frame_b64)
                        if live_detect and camera_service.latest_frame_cv is not None:
                            detected_items = neural_detector.detect(camera_service.latest_frame_cv)
                            h, w = camera_service.latest_frame_cv.shape[:2]
                            boxes = []
                            for item in detected_items:
                                bx, by, bw, bh = item.get("bbox", (0, 0, 0, 0))
                                boxes.append({
                                    "name": item["name"],
                                    "confidence": round(float(item["confidence"]), 2),
                                    "location": item.get("location", ""),
                                    "spatial_relationship": item.get("spatial_relationship", ""),
                                    "rel_x": round(bx / max(w, 1), 4),
                                    "rel_y": round(by / max(h, 1), 4),
                                    "rel_w": round(bw / max(w, 1), 4),
                                    "rel_h": round(bh / max(h, 1), 4)
                                })
                            await websocket.send_json({
                                "type": "live_detections",
                                "boxes": boxes,
                                "frame_w": w,
                                "frame_h": h
                            })

                elif msg_type == "audio_chunk":
                    audio_b64 = data.get("audio_base64", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        transcription = stt_service.transcribe_audio_bytes(audio_bytes)
                        if transcription:
                            await process_user_query(transcription, is_voice=True)

                elif msg_type == "barge_in":
                    tts_service.cancel()
                    await websocket.send_json({"type": "state_change", "state": "LISTENING"})

                elif msg_type == "camera_toggle":
                    continuous = data.get("continuous", False)
                    if camera_service.is_active:
                        camera_service.stop_camera()
                    else:
                        camera_service.start_camera(continuous=continuous)
                    await manager.broadcast_json({
                        "type": "camera_status",
                        "active": camera_service.is_active,
                        "continuous": camera_service.continuous_mode
                    })

                elif msg_type == "analyze_camera":
                    frame_b64 = data.get("frame_base64")
                    if frame_b64:
                        camera_service.update_frame_from_base64(frame_b64)
                    res = await visual_memory_engine.analyze_frame_and_extract_memory(frame_b64)
                    await websocket.send_json({"type": "visual_analysis_result", "data": res})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong", "clock": get_system_time()})

            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket unhandled disconnect: {e}")
        manager.disconnect(websocket)

# Serve built frontend with no-cache headers for index.html
@app.get("/")
async def serve_index():
    index_file = Path(settings.BASE_DIR) / "frontend" / "dist" / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return JSONResponse({"status": "error", "message": "Frontend build not found"}, status_code=404)

frontend_assets = Path(settings.BASE_DIR) / "frontend" / "dist" / "assets"
if frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="assets")

frontend_dist = Path(settings.BASE_DIR) / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
