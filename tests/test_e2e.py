import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "AEGIS" in data["app_name"]
    assert "time" in data["clock"]

def test_chat_system_time():
    resp = client.post("/api/chat", json={"text": "What time is it?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "The current time is" in data["response"]
    assert data["verified"] is True

def test_chat_remind_without_time():
    # SIH Rule: When no time is provided, AURA must ask "When should I remind you?"
    resp = client.post("/api/chat", json={"text": "Remind me to submit my assignment"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "When should I remind you?"

def test_chat_visual_memory_query():
    resp = client.post("/api/chat", json={"text": "Where is the clock?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert "clock" in data["response"].lower()

def test_chat_create_python_calculator(tmp_path):
    resp = client.post("/api/chat", json={"text": "Create a Python calculator on my Desktop"})
    assert resp.status_code == 200
    data = resp.json()
    assert "calculator.py" in data["response"]
    assert data["verified"] is True

def test_chat_hello_greeting():
    resp = client.post("/api/chat", json={"text": "Hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["response"]) > 0
    assert "Hey!" in data["response"] or "help" in data["response"].lower()
    assert data["verified"] is True

def test_chat_how_are_you():
    resp = client.post("/api/chat", json={"text": "How are you?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "great" in data["response"].lower()
    assert data["verified"] is True

def test_chat_what_is_the_time_right_now():
    # Tests Error 2: "What is the time right now"
    resp = client.post("/api/chat", json={"text": "What is the time right now"})
    assert resp.status_code == 200
    data = resp.json()
    assert "The current time is" in data["response"]
    assert data["verified"] is True

def test_chat_who_is_albert_einstein():
    # Tests Error 3: "Who is Albert Einstein?"
    resp = client.post("/api/chat", json={"text": "Who is Albert Einstein?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Einstein" in data["response"] or "physicist" in data["response"].lower()
    assert data["verified"] is True

def test_chat_set_reminder_specific_time():
    # Tests Error 4 & 5: Reminders with zero-padded minutes e.g. 12:07 AM
    resp = client.post("/api/chat", json={"text": "Remind me at 12:07 AM to sleep"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Reminder set" in data["response"]
    assert "12:07 AM" in data["response"]
    assert "/" not in data["response"]  # Ensure no 12/7AM format
    assert data["verified"] is True

def test_stt_normalization():
    # Tests Error 5: Normalization of 12/7AM -> 12:07 AM
    from backend.services.stt import normalize_transcription_text
    assert normalize_transcription_text("12/7 AM") == "12:07 AM"
    assert normalize_transcription_text("12/07AM") == "12:07 AM"
    assert normalize_transcription_text("5.30 PM") == "5:30 PM"

def test_chat_math_multiplication():
    # Tests "2*2"
    resp = client.post("/api/chat", json={"text": "2*2"})
    assert resp.status_code == 200
    data = resp.json()
    assert "4" in data["response"]
    assert data["verified"] is True

def test_chat_math_natural_expression():
    # Tests "What is 25 * 4?"
    resp = client.post("/api/chat", json={"text": "What is 25 * 4?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "100" in data["response"]
    assert data["verified"] is True



