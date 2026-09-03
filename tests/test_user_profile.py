import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.memory import memory_store

client = TestClient(app)

def test_user_profile_and_memory_sync():
    # 1. Get initial default profile
    res = client.get("/api/user/profile")
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data

    # 2. Login with user profile
    login_payload = {
        "name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "auth_provider": "google",
        "role": "Robotics Researcher",
        "personal_notes": "Prefers spoken feedback and daily summaries."
    }
    login_res = client.post("/api/user/login", json=login_payload)
    assert login_res.status_code == 200
    profile_data = login_res.json()
    assert profile_data["status"] == "success"
    assert profile_data["profile"]["name"] == "Jordan Lee"

    # 3. Verify personal memory was automatically synced
    mems = memory_store.get_all_memories()
    mem_map = {m["key"]: m["value"] for m in mems}
    assert mem_map.get("user_name") == "Jordan Lee"
    assert mem_map.get("user_email") == "jordan.lee@example.com"
    assert mem_map.get("user_role") == "Robotics Researcher"
    assert "spoken feedback" in mem_map.get("user_notes", "")

    # 4. Verify GET /api/user/profile returns the synced user
    check_res = client.get("/api/user/profile")
    assert check_res.status_code == 200
    assert check_res.json()["name"] == "Jordan Lee"
