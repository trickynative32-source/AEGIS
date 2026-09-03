import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.memory import memory_store

client = TestClient(app)

def test_full_auth_lifecycle():
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"elena.{unique_id}@blackmesa.org"

    # 1. Register a new user with full personal, emergency, and location information
    reg_payload = {
        "name": "Dr. Elena Vance",
        "email": test_email,
        "password": "SecurePassword987!",
        "role": "Principal Quantum Physicist",
        "phone": "+1-555-0199",
        "location": "New Mexico, Sector C",
        "emergency_contact_name": "Eli Vance",
        "emergency_contact_phone": "+1-555-0142",
        "bio": "Lead researcher focusing on visual teleportation and spatial resonance.",
        "personal_notes": "Speak softly, prioritize critical telemetry and time alerts."
    }

    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200, reg_res.text
    data = reg_res.json()
    assert data["status"] == "success"
    token = data["token"]
    assert token and len(token) > 20
    user = data["user"]
    assert user["name"] == "Dr. Elena Vance"
    assert user["location"] == "New Mexico, Sector C"
    assert user["emergency_contact_name"] == "Eli Vance"

    # 2. Verify AEGIS memory automatically synced all info
    mems = memory_store.get_all_memories()
    mem_map = {m["key"]: m["value"] for m in mems}
    assert mem_map.get("user_name") == "Dr. Elena Vance"
    assert mem_map.get("user_location") == "New Mexico, Sector C"
    assert "Eli Vance" in mem_map.get("user_emergency_contact", "")
    assert "Quantum Physicist" in mem_map.get("user_role", "")

    # 3. Test Invalid Login
    bad_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 4. Test Valid Login
    good_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword987!"
    })
    assert good_login.status_code == 200
    login_data = good_login.json()
    assert login_data["status"] == "success"
    fresh_token = login_data["token"]

    # 5. Test Authenticated Profile Route /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {fresh_token}"})
    assert me_res.status_code == 200
    me_user = me_res.json()["user"]
    assert me_user["email"] == test_email

    # 6. Test Google Login with Full Profile Data
    g_email = f"gordon.{unique_id}@gmail.com"
    google_res = client.post("/api/auth/google", json={
        "name": "Gordon Freeman",
        "email": g_email,
        "avatar_url": "https://example.com/gordon.jpg",
        "role": "Hazardous Operations Specialist",
        "location": "Seattle, WA",
        "emergency_contact_name": "Isaac Kleiner",
        "emergency_contact_phone": "+1-555-0177",
        "personal_notes": "Prefers silence and non-verbal spatial cues."
    })
    assert google_res.status_code == 200
    g_data = google_res.json()
    assert g_data["user"]["name"] == "Gordon Freeman"
    assert g_data["user"]["auth_provider"] == "google"

    # Verify memory updated to new user
    mems = memory_store.get_all_memories()
    mem_map = {m["key"]: m["value"] for m in mems}
    assert mem_map.get("user_name") == "Gordon Freeman"
    assert "Isaac Kleiner" in mem_map.get("user_emergency_contact", "")
