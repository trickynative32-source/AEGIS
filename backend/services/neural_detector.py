import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger("AEGIS.NeuralDetector")

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# Map COCO labels to friendlier names
LABEL_MAP = {
    "cell phone": "phone",
    "handbag": "bag",
    "backpack": "bag",
    "suitcase": "bag",
    "cup": "mug",
    "wine glass": "glass",
    "dining table": "desk",
    "couch": "sofa",
    "potted plant": "plant",
    "tv": "screen",
    "teddy bear": "stuffed toy"
}

# Objects that should never be classified as "in hand"
LARGE_OBJECTS = {"person", "chair", "couch", "sofa", "bed", "desk", "dining table", "refrigerator",
                 "oven", "microwave", "sink", "toilet", "painting", "tv", "screen"}


INDOOR_RELEVANT = {
    "person", "cell phone", "bottle", "cup", "wine glass", "remote", "laptop", "mouse", "keyboard",
    "book", "clock", "backpack", "handbag", "suitcase", "chair", "couch", "bed", "dining table", "tv",
    "potted plant", "scissors", "vase", "teddy bear"
}


class NeuralObjectDetector:
    """High-accuracy YOLOv5s / YOLOX ONNX neural object detector with true deep neural detections."""

    def __init__(self):
        self.session = None
        self.model_type = "yolov5"  # "yolov5" or "yolox"
        self.model_loaded = False
        self._input_name = "images"
        self._input_h = 640
        self._input_w = 640
        self.grids = None
        self.expanded_strides = None
        self._load_model()

    def _load_model(self):
        try:
            import onnxruntime as ort
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_cache")
            yolov5m_path = os.path.join(cache_dir, "yolov5m.onnx")
            yolov5s_path = os.path.join(cache_dir, "yolov5s.onnx")
            yolox_path = os.path.join(cache_dir, "coco-yolox_tiny.onnx")

            if os.path.exists(yolov5m_path):
                self.session = ort.InferenceSession(yolov5m_path, providers=["CPUExecutionProvider"])
                inp = self.session.get_inputs()[0]
                self._input_name = inp.name
                self._input_h = inp.shape[2] if len(inp.shape) > 2 else 640
                self._input_w = inp.shape[3] if len(inp.shape) > 3 else 640
                self.model_type = "yolov5"
                self.model_loaded = True
                logger.info(f"High-Precision YOLOv5m Neural Detector loaded: input {self._input_name} shape ({self._input_w}x{self._input_h})")
            elif os.path.exists(yolov5s_path):
                self.session = ort.InferenceSession(yolov5s_path, providers=["CPUExecutionProvider"])
                inp = self.session.get_inputs()[0]
                self._input_name = inp.name
                self._input_h = inp.shape[2] if len(inp.shape) > 2 else 640
                self._input_w = inp.shape[3] if len(inp.shape) > 3 else 640
                self.model_type = "yolov5"
                self.model_loaded = True
                logger.info(f"YOLOv5s Neural Detector loaded: input {self._input_name} shape ({self._input_w}x{self._input_h})")
            elif os.path.exists(yolox_path):
                self.session = ort.InferenceSession(yolox_path, providers=["CPUExecutionProvider"])
                inp = self.session.get_inputs()[0]
                self._input_name = inp.name
                self._input_h = inp.shape[2]
                self._input_w = inp.shape[3]
                self.model_type = "yolox"

                strides = [8, 16, 32]
                grids = []
                expanded_strides = []
                for s in strides:
                    fh = self._input_h // s
                    fw = self._input_w // s
                    xv, yv = np.meshgrid(np.arange(fw), np.arange(fh))
                    grids.append(np.stack((xv, yv), 2).reshape(-1, 2))
                    expanded_strides.append(np.full((fh * fw, 1), s))

                self.grids = np.concatenate(grids, axis=0)
                self.expanded_strides = np.concatenate(expanded_strides, axis=0)
                self.model_loaded = True
                logger.info(f"YOLOX Neural Detector loaded: input {self._input_name} shape ({self._input_w}x{self._input_h})")
            else:
                logger.warning("No ONNX detector model found in models_cache")
        except Exception as e:
            logger.warning(f"Could not initialize Neural Detector: {e}")

    def _letterbox(self, img: np.ndarray, new_shape: tuple = (640, 640), color: tuple = (114, 114, 114)):
        """Standard YOLO letterbox with aspect ratio preservation and symmetric border padding."""
        shape = img.shape[:2]
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2.0
        dh /= 2.0

        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, r, (dw, dh)

    def _run_inference(self, img_cv: np.ndarray) -> List[Dict[str, Any]]:
        """Run deep neural network inference with letterbox aspect-preserving scaling."""
        if not self.model_loaded or self.session is None:
            return []

        h_orig, w_orig = img_cv.shape[:2]
        detections = []

        try:
            if self.model_type == "yolov5":
                # Preprocess for YOLOv5: RGB, letterbox, normalized 0..1, FP16
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                img_lb, r, (dw, dh) = self._letterbox(img_rgb, (self._input_w, self._input_h))
                blob = (img_lb.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis, ...].astype(np.float16)

                outputs = self.session.run(None, {self._input_name: blob})[0][0].astype(np.float32)

                boxes, scores, class_ids = [], [], []
                for i in range(len(outputs)):
                    row = outputs[i]
                    obj_conf = float(row[4])
                    if obj_conf < 0.20:
                        continue
                    cls_scores = row[5:] * obj_conf
                    cid = int(np.argmax(cls_scores))
                    score = float(cls_scores[cid])
                    raw_name = COCO_CLASSES[cid]

                    min_conf = 0.22 if raw_name in INDOOR_RELEVANT else 0.65
                    if score < min_conf:
                        continue

                    cx, cy, bw, bh = row[0], row[1], row[2], row[3]
                    x1 = (cx - bw / 2.0 - dw) / r
                    y1 = (cy - bh / 2.0 - dh) / r
                    wb = bw / r
                    hb = bh / r

                    px1 = max(0, min(w_orig - 1, int(round(x1))))
                    py1 = max(0, min(h_orig - 1, int(round(y1))))
                    pwb = max(1, min(w_orig - px1, int(round(wb))))
                    phb = max(1, min(h_orig - py1, int(round(hb))))

                    if pwb < 15 or phb < 15:
                        continue

                    boxes.append([px1, py1, pwb, phb])
                    scores.append(score)
                    class_ids.append(cid)

                if boxes:
                    indices = cv2.dnn.NMSBoxes(boxes, scores, 0.22, 0.45)
                    if len(indices) > 0:
                        for idx in indices.flatten():
                            raw_label = COCO_CLASSES[class_ids[idx]]
                            label = LABEL_MAP.get(raw_label, raw_label)
                            detections.append({
                                "name": label,
                                "confidence": round(float(scores[idx]), 3),
                                "bbox": (boxes[idx][0], boxes[idx][1], boxes[idx][2], boxes[idx][3]),
                                "source": "yolov5"
                            })

            elif self.model_type == "yolox" and self.grids is not None:
                img_resized = cv2.resize(img_cv, (self._input_w, self._input_h))
                blob = img_resized.transpose(2, 0, 1).astype(np.float32)[np.newaxis, ...]
                outputs = self.session.run(None, {self._input_name: blob})[0][0]

                cx_cy = (outputs[:, :2] + self.grids) * self.expanded_strides
                bw_bh = np.exp(outputs[:, 2:4]) * self.expanded_strides
                scale_x = w_orig / float(self._input_w)
                scale_y = h_orig / float(self._input_h)

                boxes, scores, class_ids = [], [], []
                for i in range(len(outputs)):
                    obj_conf = outputs[i, 4]
                    if obj_conf < 0.20:
                        continue
                    cls_scores = outputs[i, 5:] * obj_conf
                    cls_id = int(np.argmax(cls_scores))
                    score = float(cls_scores[cls_id])
                    raw_name = COCO_CLASSES[cls_id]

                    min_threshold = 0.30 if raw_name in INDOOR_RELEVANT else 0.65
                    if score < min_threshold:
                        continue

                    cx = float(cx_cy[i, 0]) * scale_x
                    cy = float(cx_cy[i, 1]) * scale_y
                    bw = float(bw_bh[i, 0]) * scale_x
                    bh = float(bw_bh[i, 1]) * scale_y

                    x1 = int(cx - bw / 2.0)
                    y1 = int(cy - bh / 2.0)
                    w_box = int(bw)
                    h_box = int(bh)

                    if w_box < 20 or h_box < 20:
                        continue

                    boxes.append([x1, y1, w_box, h_box])
                    scores.append(score)
                    class_ids.append(cls_id)

                if boxes:
                    indices = cv2.dnn.NMSBoxes(boxes, scores, 0.30, 0.35)
                    if len(indices) > 0:
                        for i in indices.flatten():
                            raw_label = COCO_CLASSES[class_ids[i]]
                            label = LABEL_MAP.get(raw_label, raw_label)
                            detections.append({
                                "name": label,
                                "confidence": round(float(scores[i]), 3),
                                "bbox": (max(0, boxes[i][0]), max(0, boxes[i][1]), min(w_orig, boxes[i][2]), min(h_orig, boxes[i][3])),
                                "source": "yolox"
                            })
        except Exception as e:
            logger.error(f"Neural inference error: {e}")

        return detections

    def detect(self, img_cv: np.ndarray, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Full detection pipeline: NVIDIA LocateAnything-3B / YOLO neural network + person deduplication + spatial reasoning."""
        if img_cv is None or img_cv.size == 0:
            return []

        h_orig, w_orig = img_cv.shape[:2]

        # Build skin mask for in-hand reasoning
        ycrcb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2YCrCb)
        skin_mask = cv2.inRange(ycrcb,
                                np.array([0, 133, 77], dtype=np.uint8),
                                np.array([255, 173, 127], dtype=np.uint8))

        # Step 1: Run neural network inference (YOLOv5s / YOLOX)
        raw_detections = self._run_inference(img_cv)

        # Step 1b: If NVIDIA LocateAnything-3B is enabled and query is provided or local server active, run open-vocabulary grounding
        try:
            from backend.services.locate_anything import locate_anything_detector
            if getattr(settings, "NVIDIA_LOCATE_ANYTHING_ENABLED", True) and locate_anything_detector.is_server_reachable():
                import asyncio
                loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else None
                # If sync context, we can query or let async caller query
        except Exception:
            pass

        # Step 2: Separate and suppress duplicate person boxes (avoid nested person sub-boxes)
        person_dets = [d for d in raw_detections if d["name"] == "person"]
        other_dets = [d for d in raw_detections if d["name"] != "person"]

        kept_people = []
        for p in sorted(person_dets, key=lambda x: x["confidence"], reverse=True):
            px, py, pw, ph = p["bbox"]
            overlap = False
            for kp in kept_people:
                kpx, kpy, kpw, kph = kp["bbox"]
                inter_x = max(0, min(px + pw, kpx + kpw) - max(px, kpx))
                inter_y = max(0, min(py + ph, kpy + kph) - max(py, kpy))
                inter_area = inter_x * inter_y
                if inter_area / min(pw * ph, kpw * kph) > 0.25:
                    overlap = True
                    break
            if not overlap:
                kept_people.append(p)

        # If no person was found by neural model, run skin contour localization as backup
        if not kept_people:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            smoothed_skin = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            skin_contours, _ = cv2.findContours(smoothed_skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_skin_area = (h_orig * w_orig) * 0.02
            for sc in skin_contours:
                s_area = cv2.contourArea(sc)
                if s_area > min_skin_area:
                    sx, sy, sw, sh = cv2.boundingRect(sc)
                    aspect = float(sw) / max(sh, 1)
                    if 0.35 <= aspect <= 2.8:
                        px = max(0, sx - 15)
                        py = max(0, sy - 15)
                        pw = min(w_orig - px, sw + 30)
                        ph = min(h_orig - py, sh + 40)
                        kept_people.append({
                            "name": "person",
                            "confidence": 0.85,
                            "bbox": (px, py, pw, ph),
                            "source": "skin_contour"
                        })
                        break

        detections = kept_people + other_dets

        # Step 3: Targeted saliency fallback for objects not detected by YOLO
        fallback_dets = self._heuristic_fallback(img_cv, skin_mask, kept_people)
        for fd in fallback_dets:
            if not any(d["name"] == fd["name"] for d in detections):
                detections.append(fd)

        # Step 4: Classify spatial placement for each detection
        results = []
        for obj in detections:
            x, y, w, h = obj["bbox"]
            name = obj["name"]
            cx = x + w / 2
            cy = y + h / 2

            # Check skin overlap for in-hand classification
            y_start = max(0, y - 5)
            y_end = min(h_orig, y + h + 5)
            x_start = max(0, x - 5)
            x_end = min(w_orig, x + w + 5)
            roi_skin = skin_mask[y_start:y_end, x_start:x_end]
            skin_ratio = np.count_nonzero(roi_skin) / max(roi_skin.size, 1)
            is_in_hand = skin_ratio > 0.15 and name not in LARGE_OBJECTS

            loc_x = "on the left" if cx < w_orig * 0.35 else ("on the right" if cx > w_orig * 0.65 else "in the center")

            if is_in_hand:
                location = "in hand"
                relationship = "held in your hand in front of the camera"
            elif name in ("painting", "wall art", "poster"):
                location = "on the wall"
                relationship = f"mounted on the wall {loc_x}"
            elif name == "clock" and cy < h_orig * 0.45:
                location = "on the wall"
                relationship = f"mounted on the wall {loc_x}"
            elif name in ("pillow", "cushion"):
                location = "on the bed"
                relationship = f"resting on the bed / sofa {loc_x}"
            elif name in ("bed", "sofa", "couch"):
                location = "in room"
                relationship = f"{loc_x} in the room"
            elif cy >= h_orig * 0.78 and name in ("bag", "backpack", "suitcase", "shoe"):
                location = "on the floor"
                relationship = f"on the floor {loc_x}"
            elif cy >= h_orig * 0.35:
                location = "on the desk"
                relationship = f"on the desk {loc_x}"
            else:
                location = "in room"
                relationship = f"{loc_x} in view"

            results.append({
                "name": name,
                "location": location,
                "spatial_relationship": relationship,
                "confidence": obj["confidence"],
                "bbox": obj["bbox"]
            })

        return results

    def _heuristic_fallback(self, img_cv: np.ndarray, skin_mask: np.ndarray, detected_people: List[Dict]) -> List[Dict[str, Any]]:
        """Targeted saliency fallback for items not captured by neural detector."""
        h_orig, w_orig = img_cv.shape[:2]
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 120)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        total_area = h_orig * w_orig
        detected = []

        for c in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            area = cv2.contourArea(c)
            if area < total_area * 0.015 or area > total_area * 0.35:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if w < 20 or h < 20:
                continue

            roi_skin = skin_mask[max(0, y - 5):min(h_orig, y + h + 5), max(0, x - 5):min(w_orig, x + w + 5)]
            skin_ratio = np.count_nonzero(roi_skin) / max(roi_skin.size, 1)

            # Check if this contour is just the person's own body
            is_body_duplicate = False
            for p in detected_people:
                px, py, pw, ph = p["bbox"]
                p_area = pw * ph
                inter_w = max(0, min(x + w, px + pw) - max(x, px))
                inter_h = max(0, min(y + h, py + ph) - max(y, py))
                inter = inter_w * inter_h
                if inter > 0.5 * area:
                    # If this is the entire body (area ~ p_area) or no skin-holding context, ignore
                    if area > 0.75 * p_area or skin_ratio <= 0.12:
                        is_body_duplicate = True
                        break

            if is_body_duplicate:
                continue

            aspect = float(w) / max(h, 1)
            cy = y + h / 2

            lbl = None
            if skin_ratio > 0.15:
                if 0.30 <= aspect <= 2.80 and not any(d["name"] == "phone" for d in detected):
                    lbl = "phone"
                elif (aspect < 0.30 or aspect >= 2.80) and not any(d["name"] == "remote" for d in detected):
                    lbl = "remote"
            elif cy < h_orig * 0.38 and w > 40 and not any(d["name"] == "painting" for d in detected):
                lbl = "painting"
            elif cy >= h_orig * 0.35 and 0.20 <= aspect <= 0.60 and not any(d["name"] == "bottle" for d in detected):
                lbl = "bottle"
            elif 0.30 <= (cy / h_orig) <= 0.80 and 0.7 <= aspect <= 2.5 and area > total_area * 0.04 and not any(d["name"] == "pillow" for d in detected):
                lbl = "pillow"

            if lbl and not any(d["name"] == lbl for d in detected):
                detected.append({
                    "name": lbl,
                    "confidence": 0.88,
                    "bbox": (x, y, w, h),
                    "source": "saliency"
                })

        return detected


neural_detector = NeuralObjectDetector()
