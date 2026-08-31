import pytest
import datetime
from backend.services.visual_memory import visual_memory_engine
from backend.database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_store_and_query_visual_memory():
    # Store observation: clock on blue wall
    res = visual_memory_engine.store_observation(
        object_name="clock",
        location_context="blue wall",
        room="study",
        spatial_relationship="near the picture frame",
        confidence=0.95
    )
    assert res["status"] in ["created", "updated"]

    # Store observation: laptop on table
    visual_memory_engine.store_observation(
        object_name="laptop",
        location_context="table",
        room="study",
        spatial_relationship="near the window",
        confidence=0.92
    )

    # Query where is the clock
    q_clock = visual_memory_engine.query_object_location("where is the clock")
    assert q_clock["found"] is True
    assert "clock" in q_clock["message"].lower()
    assert "blue wall" in q_clock["message"].lower()

    # Query where is my laptop
    q_laptop = visual_memory_engine.query_object_location("where is my laptop")
    assert q_laptop["found"] is True
    assert "table" in q_laptop["message"].lower()
    assert "near the window" in q_laptop["message"].lower()

    # Query room
    q_room = visual_memory_engine.query_object_location("what room am i in")
    assert q_room["found"] is True
    assert "study" in q_room["message"].lower()

def test_object_movement_update():
    # Update clock location
    visual_memory_engine.store_observation(
        object_name="bag",
        location_context="beside the chair",
        room="study",
        spatial_relationship="on the floor",
        confidence=0.90
    )

    q1 = visual_memory_engine.query_object_location("where did you see my bag")
    assert q1["found"] is True
    assert "beside the chair" in q1["message"].lower()

@pytest.mark.asyncio
async def test_multi_person_and_multi_object_detection():
    import cv2
    import numpy as np
    import base64
    from backend.services.vision import camera_service

    # Create synthetic frame with 2 distinct people regions + multiple objects
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Person 1 (left)
    img[80:260, 80:220] = [120, 140, 200]
    # Person 2 (right)
    img[80:260, 420:560] = [120, 140, 200]
    # Object 1 (center)
    img[320:440, 260:380] = [200, 200, 200]

    _, buf = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(buf).decode('utf-8')

    # Update camera service frame
    camera_service.update_frame_from_base64(b64)
    person_res = camera_service.detect_person_local()
    assert person_res["detected"] is True
    assert person_res["count"] == 2
    assert "2 people" in person_res["message"]

    # Run visual memory frame analysis
    analysis_res = await visual_memory_engine.analyze_frame_and_extract_memory(b64)
    assert analysis_res["people_count"] == 2
    assert len(analysis_res["objects"]) >= 2

@pytest.mark.asyncio
async def test_closed_camera_shutter_detection():
    import cv2
    import numpy as np
    import base64
    from backend.services.vision import camera_service

    # Test 1: Solid Grey Windows privacy shutter frame
    shutter_frame = np.full((480, 640, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode('.jpg', shutter_frame)
    b64_shutter = base64.b64encode(buf).decode('utf-8')

    camera_service.update_frame_from_base64(b64_shutter)
    res_shutter = await visual_memory_engine.analyze_frame_and_extract_memory(b64_shutter)
    assert res_shutter["status"] == "camera_covered"
    assert "shutter is closed" in res_shutter["message"].lower() or "covered" in res_shutter["message"].lower()

    # Test 2: Pitch black frame
    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf_black = cv2.imencode('.jpg', black_frame)
    b64_black = base64.b64encode(buf_black).decode('utf-8')

    camera_service.update_frame_from_base64(b64_black)
    res_black = await visual_memory_engine.analyze_frame_and_extract_memory(b64_black)
    assert res_black["status"] == "camera_covered"

def test_everyday_objects_location_recall():
    # 1. Store Phone observation
    visual_memory_engine.store_observation(
        object_name="phone",
        location_context="desk next to the keyboard",
        room="workspace",
        spatial_relationship="on the left side",
        confidence=0.95
    )

    # 2. Store Remote observation
    visual_memory_engine.store_observation(
        object_name="remote",
        location_context="coffee table",
        room="living room",
        spatial_relationship="next to the TV",
        confidence=0.92
    )

    # 3. Query Phone
    q_phone = visual_memory_engine.query_object_location("where is my phone?")
    assert q_phone["found"] is True
    assert "phone" in q_phone["message"].lower()
    assert "desk next to the keyboard" in q_phone["message"].lower()

    # 4. Query Remote
    q_remote = visual_memory_engine.query_object_location("where did you see my remote?")
    assert q_remote["found"] is True
    assert "remote" in q_remote["message"].lower()
    assert "coffee table" in q_remote["message"].lower()

@pytest.mark.asyncio
async def test_painting_wall_and_in_hand_object_spatial_recognition():
    import cv2
    import numpy as np
    import base64

    # 1. Test query for painting on wall
    visual_memory_engine.store_observation(
        object_name="painting",
        location_context="on wall",
        room="study room",
        spatial_relationship="mounted on the wall behind the desk",
        confidence=0.96
    )
    q_art = visual_memory_engine.query_object_location("where is the painting?")
    assert q_art["found"] is True
    assert "painting" in q_art["message"].lower()
    assert "wall" in q_art["message"].lower()

    # 2. Test query for phone held in hand
    visual_memory_engine.store_observation(
        object_name="phone",
        location_context="in hand",
        room="study room",
        spatial_relationship="held in your hand in front of the camera",
        confidence=0.95
    )
    q_phone = visual_memory_engine.query_object_location("where is my phone?")
    assert q_phone["found"] is True
    assert "hand" in q_phone["message"].lower()

    # 3. Test local CV multi-layer spatial segmentation with painting and in-hand phone
    h, w = 480, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # Upper painting (on wall)
    cv2.rectangle(img, (180, 40), (460, 160), (180, 150, 100), -1)
    # Middle skin + phone (in hand)
    cv2.rectangle(img, (100, 220), (220, 340), [120, 140, 200], -1)
    cv2.rectangle(img, (120, 230), (180, 330), (30, 30, 30), -1)
    # Lower bottle (on desk)
    cv2.rectangle(img, (480, 320), (540, 460), (200, 100, 50), -1)

    _, buf = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(buf).decode('utf-8')

    res = await visual_memory_engine.analyze_frame_and_extract_memory(b64)
    assert res["status"] in ["local_cv", "neural_cv", "success"]
    assert "painting" in res["objects"]
    assert "phone" in res["objects"] or "item in hand" in res["objects"]
    assert "bottle" in res["objects"] or "item" in res["objects"]

@pytest.mark.asyncio
async def test_pillow_bottle_remote_and_paintings_detection():
    import cv2
    import numpy as np
    import base64

    # 1. Store observation for pillow on bed
    visual_memory_engine.store_observation(
        object_name="pillow",
        location_context="bed",
        room="bedroom",
        spatial_relationship="resting on the head of the bed",
        confidence=0.94
    )
    q_pillow = visual_memory_engine.query_object_location("where is the pillow?")
    assert q_pillow["found"] is True
    assert "pillow" in q_pillow["message"].lower()
    assert "bed" in q_pillow["message"].lower()

    # 2. Store observation for remote in hand
    visual_memory_engine.store_observation(
        object_name="remote",
        location_context="in hand",
        room="living room",
        spatial_relationship="held in your hand in front of the camera",
        confidence=0.93
    )
    q_remote = visual_memory_engine.query_object_location("where is my remote?")
    assert q_remote["found"] is True
    assert "remote" in q_remote["message"].lower()
    assert "hand" in q_remote["message"].lower()

    # 3. Test Local CV classification with pillow, remote, and bottle
    h, w = 480, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # Pillow contour (middle soft fabric block)
    cv2.rectangle(img, (200, 180), (380, 280), (220, 220, 220), -1)
    # Remote (in hand)
    cv2.rectangle(img, (80, 200), (160, 320), [120, 140, 200], -1)
    cv2.rectangle(img, (100, 210), (140, 310), (20, 20, 20), -1)
    # Bottle (on desk)
    cv2.rectangle(img, (480, 280), (540, 420), (180, 100, 60), -1)

    _, buf = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(buf).decode('utf-8')

    res = await visual_memory_engine.analyze_frame_and_extract_memory(b64)
    assert res["status"] in ["local_cv", "neural_cv", "success"]
    assert len(res["objects"]) >= 2




