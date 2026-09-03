import hashlib
import secrets
import json
from typing import Tuple, Optional, Dict, Any
from backend.models import UserProfile
from backend.services.memory import memory_store

ITERATIONS = 100000

def hash_password(password: str) -> Tuple[str, str]:
    """Generates a random salt and a secure PBKDF2 HMAC SHA-256 hash."""
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return salt, hash_bytes.hex()

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verifies a password against the stored PBKDF2 hash using constant-time comparison."""
    if not salt or not expected_hash:
        return False
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return secrets.compare_digest(hash_bytes.hex(), expected_hash)

def generate_session_token() -> str:
    """Generates a cryptographically strong 256-bit URL-safe session token."""
    return secrets.token_urlsafe(32)

def sync_user_to_memory(profile: UserProfile):
    """Syncs user profile details directly into AEGIS long-term memory so the assistant knows the user."""
    if not profile:
        return
    
    if profile.name:
        memory_store.set_memory("user_name", profile.name, category="profile")
    if profile.email:
        memory_store.set_memory("user_email", profile.email, category="profile")
    if profile.role:
        memory_store.set_memory("user_role", profile.role, category="profile")
    if profile.location:
        memory_store.set_memory("user_location", profile.location, category="profile")
    if profile.phone:
        memory_store.set_memory("user_phone", profile.phone, category="profile")
    if profile.emergency_contact_name or profile.emergency_contact_phone:
        contact_str = f"{profile.emergency_contact_name or 'Emergency Contact'}: {profile.emergency_contact_phone or 'N/A'}"
        memory_store.set_memory("user_emergency_contact", contact_str, category="profile")
    if profile.bio:
        memory_store.set_memory("user_bio", profile.bio, category="profile")
    if profile.personal_notes:
        memory_store.set_memory("user_notes", profile.personal_notes, category="profile")

def serialize_user_profile(profile: Optional[UserProfile]) -> Dict[str, Any]:
    """Serializes a UserProfile model instance to a clean JSON dict, omitting password and salt."""
    if not profile:
        return {
            "user_id": "guest",
            "name": "Guest Explorer",
            "email": None,
            "avatar_url": None,
            "auth_provider": "guest",
            "role": "Guest",
            "phone": None,
            "location": None,
            "timezone": "Asia/Kolkata",
            "emergency_contact_name": None,
            "emergency_contact_phone": None,
            "bio": None,
            "personal_notes": None,
            "preferences": {},
            "accessibility_settings": {},
            "is_authenticated": False
        }

    prefs = {}
    if profile.preferences_json:
        try:
            prefs = json.loads(profile.preferences_json)
        except Exception:
            pass

    access_settings = {}
    if profile.accessibility_settings_json:
        try:
            access_settings = json.loads(profile.accessibility_settings_json)
        except Exception:
            pass

    return {
        "user_id": profile.user_id,
        "name": profile.name,
        "email": profile.email,
        "avatar_url": profile.avatar_url,
        "auth_provider": profile.auth_provider,
        "role": profile.role or "User",
        "phone": profile.phone,
        "location": profile.location,
        "timezone": profile.timezone or "Asia/Kolkata",
        "emergency_contact_name": profile.emergency_contact_name,
        "emergency_contact_phone": profile.emergency_contact_phone,
        "bio": profile.bio,
        "personal_notes": profile.personal_notes,
        "preferences": prefs,
        "accessibility_settings": access_settings,
        "last_login": profile.last_login.isoformat() if profile.last_login else None,
        "is_authenticated": profile.auth_provider != "guest"
    }
