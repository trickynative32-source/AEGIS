import cv2
import time
import base64
import logging
import threading
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from backend.config import settings

logger = logging.getLogger("AEGIS.Vision")

def is_frame_covered_or_blank(frame_cv) -> Tuple[bool, str]:
    """Detects if camera lens is covered, physical shutter is closed, pitch black, or Windows placeholder."""
    if frame_cv is None:
        return True, "No camera frame is currently available. Please ensure the camera is turned on."

    try:
        gray = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2GRAY)
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))
        
        edges = cv2.Canny(gray, 40, 120)
        edge_density = float(np.count_nonzero(edges)) / (gray.shape[0] * gray.shape[1])

        # 1. Pitch black / covered with finger, cloth, or tape
        if mean_val < 18.0 and std_val < 12.0:
            return True, "The camera lens is covered or in darkness. Please uncover the camera lens or open the shutter."

        # 2. Solid flat grey / blank frame (standard Windows hardware privacy shutter)
        if std_val < 8.0:
            return True, "The camera privacy shutter is closed. Please slide open your camera shutter to enable vision."

        # 3. Windows Camera Driver Shutter with lock watermark / grey screen
        if std_val < 22.0 and edge_density < 0.003:
            return True, "The camera privacy shutter is closed. Please slide open your physical camera shutter."

        return False, ""
    except Exception as e:
        logger.warning(f"Error checking frame coverage: {e}")
        return False, ""

class CameraService:
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active: bool = False
        self.is_paused: bool = False
        self.continuous_mode: bool = False
        self.latest_frame: Optional[bytes] = None
        self.latest_frame_cv = None
        self.lock = threading.Lock()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Safe classifier loader
        self.face_cascade = None
        self.upper_body_cascade = None
        if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            try:
                cascade_path = cv2.data.haarcascades
                if cascade_path:
                    self.face_cascade = cv2.CascadeClassifier(cascade_path + 'haarcascade_frontalface_default.xml')
                    self.upper_body_cascade = cv2.CascadeClassifier(cascade_path + 'haarcascade_upperbody.xml')
            except Exception as e:
                logger.warning(f"Could not load cv2 Haar cascades: {e}")

    def update_frame_from_base64(self, frame_b64: str) -> bool:
        """Updates latest camera frame directly from frontend WebRTC/canvas capture."""
        try:
            img_bytes = base64.b64decode(frame_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                with self.lock:
                    self.latest_frame = img_bytes
                    self.latest_frame_cv = img
                    self.is_active = True
                return True
        except Exception as e:
            logger.error(f"Error updating frame from base64: {e}")
        return False

    def start_camera(self, continuous: bool = False) -> Dict[str, Any]:
        """Activates camera stream in backend without blocking browser hardware access."""
        with self.lock:
            self.is_active = True
            self.is_paused = False
            self.continuous_mode = continuous
            self.stop_event.clear()

        logger.info("Camera service activated (ready for browser WebRTC & backend frame sync).")
        return {
            "status": "started",
            "message": "Camera is active.",
            "continuous": self.continuous_mode
        }

    def start_hardware_capture_fallback(self):
        """Attempts direct OpenCV hardware capture if browser is not streaming."""
        with self.lock:
            if self.cap is not None and self.cap.isOpened():
                return
            for idx in [0, 1, 2]:
                try:
                    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0)
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        self.cap = cap
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        break
                except Exception:
                    continue

            if self.cap and self.cap.isOpened():
                if self.worker_thread is None or not self.worker_thread.is_alive():
                    self.worker_thread = threading.Thread(target=self._capture_loop, daemon=True)
                    self.worker_thread.start()

    def stop_camera(self) -> Dict[str, Any]:
        """Deactivates camera."""
        with self.lock:
            self.stop_event.set()
            self.is_active = False
            self.is_paused = False
            self.continuous_mode = False
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.latest_frame = None
            self.latest_frame_cv = None

        logger.info("Camera stopped.")
        return {"status": "stopped", "message": "Camera is turned off."}

    def pause_camera(self) -> Dict[str, Any]:
        self.is_paused = True
        return {"status": "paused", "message": "Camera paused."}

    def resume_camera(self) -> Dict[str, Any]:
        self.is_paused = False
        return {"status": "resumed", "message": "Camera resumed."}

    def _capture_loop(self):
        while not self.stop_event.is_set():
            if self.is_paused or self.cap is None:
                time.sleep(0.1)
                continue

            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    with self.lock:
                        self.latest_frame = buffer.tobytes()
                        self.latest_frame_cv = frame
                time.sleep(0.04)  # ~25 FPS
            except Exception as e:
                time.sleep(0.2)

    def get_latest_frame_bytes(self) -> Optional[bytes]:
        with self.lock:
            return self.latest_frame

    def get_latest_frame_base64(self) -> Optional[str]:
        with self.lock:
            if self.latest_frame:
                return base64.b64encode(self.latest_frame).decode("utf-8")
        return None

    def detect_person_local(self) -> Dict[str, Any]:
        """Local offline multi-person presence detector supporting 1, 2, 3+ individuals with shutter check."""
        with self.lock:
            frame = self.latest_frame_cv

        if frame is None:
            return {
                "detected": False,
                "count": 0,
                "confidence": 0.0,
                "message": "The camera is currently turned off or no video frame is available. Please enable the camera."
            }

        # Check for covered camera lens / closed privacy shutter
        is_covered, covered_msg = is_frame_covered_or_blank(frame)
        if is_covered:
            return {
                "detected": False,
                "count": 0,
                "people": [],
                "confidence": 0.0,
                "message": covered_msg
            }

        height, width = frame.shape[:2]
        people_detected = []

        # 1. Multi-Region YCrCb Skin Color Segmentation
        try:
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            lower_skin = np.array([0, 133, 77], dtype=np.uint8)
            upper_skin = np.array([255, 173, 127], dtype=np.uint8)
            skin_mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

            # Morphological smoothing to combine facial features while separating distinct people
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel, iterations=1)

            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_person_area = (height * width) * 0.015  # At least 1.5% of total frame area

            for c in contours:
                area = cv2.contourArea(c)
                if area > min_person_area:
                    x, y, w, h = cv2.boundingRect(c)
                    aspect_ratio = float(w) / h
                    # Human head/torso contour filtering
                    if 0.35 <= aspect_ratio <= 2.5:
                        center_x = x + w / 2
                        if center_x < width * 0.35:
                            pos = "on the left"
                        elif center_x > width * 0.65:
                            pos = "on the right"
                        else:
                            pos = "in the center"

                        people_detected.append({
                            "position": pos,
                            "bbox": (x, y, w, h),
                            "area": area
                        })
        except Exception as e:
            logger.warning(f"Contour person detection notice: {e}")

        person_count = len(people_detected)

        # 2. Haar Cascade Validation if available
        if person_count == 0 and self.face_cascade:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
                person_count = len(faces)
            except Exception:
                pass

        if person_count == 1:
            pos = people_detected[0]["position"] if people_detected else "in front of the camera"
            msg = f"Yes, I see 1 person {pos} in front of the camera."
            return {
                "detected": True,
                "count": 1,
                "people": people_detected,
                "confidence": 0.92,
                "message": msg
            }
        elif person_count > 1:
            positions_summary = ", ".join([f"person {i+1} {p['position']}" for i, p in enumerate(people_detected)])
            msg = f"Yes, I detect {person_count} people in front of the camera ({positions_summary})."
            return {
                "detected": True,
                "count": person_count,
                "people": people_detected,
                "confidence": 0.94,
                "message": msg
            }

        return {
            "detected": False,
            "count": 0,
            "people": [],
            "confidence": 0.85,
            "message": "No person is currently detected in front of the camera."
        }

camera_service = CameraService()
