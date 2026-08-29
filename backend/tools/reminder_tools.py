import datetime
import logging
import dateparser
from typing import Dict, Any, Optional, List
from backend.tools.registry import registry
from backend.database import SessionLocal
from backend.models import Reminder

logger = logging.getLogger("AEGIS.ReminderTools")

def format_display_time(dt: datetime.datetime, include_date: bool = True) -> str:
    """Formats datetime with zero-padded minutes and natural hour, e.g. 'Thursday, August 27 at 12:07 AM'."""
    hour = int(dt.strftime("%I"))
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p")
    time_part = f"{hour}:{minute} {ampm}"
    if include_date:
        date_part = dt.strftime("%A, %B %d")
        return f"{date_part} at {time_part}"
    return time_part

@registry.register(
    name="create_reminder",
    description="Create a user-defined reminder for a specific time or date. Must have user-specified time; never guess time.",
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "What to remind the user about (e.g. 'Submit my assignment', 'Take medicine', 'Team meeting')"
            },
            "time_str": {
                "type": "string",
                "description": "When to remind the user (e.g. 'tomorrow at 5 PM', 'in 10 minutes', 'at 8:30 AM', 'Friday at 2 PM')"
            }
        },
        "required": ["text", "time_str"]
    },
    permission_level="normal",
    category="reminders"
)
def create_reminder(text: str, time_str: Optional[str] = None) -> Dict[str, Any]:
    if not time_str or not time_str.strip():
        return {
            "status": "needs_time",
            "message": "When should I remind you?",
            "verified": False,
            "text": text
        }

    now = datetime.datetime.now()
    clean_time_str = time_str.strip().replace("/", ":").replace(".", ":")
    # Parse natural language time anchored to current local system time
    parsed_time = dateparser.parse(
        clean_time_str,
        settings={'RELATIVE_BASE': now, 'PREFER_DATES_FROM': 'future'}
    )

    if not parsed_time:
        return {
            "status": "parse_error",
            "message": f"I couldn't understand the time '{time_str}'. When should I remind you?",
            "verified": False
        }

    # If parsed time is in past for today, push to next occurrence or handle intelligently
    if parsed_time <= now and ("today" not in clean_time_str.lower() and "minute" not in clean_time_str.lower() and "second" not in clean_time_str.lower()):
        parsed_time = parsed_time + datetime.timedelta(days=1)

    db = SessionLocal()
    try:
        reminder = Reminder(
            text=text.strip(),
            reminder_time=parsed_time,
            created_at=now,
            is_active=True,
            is_completed=False
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        formatted_time = format_display_time(parsed_time, include_date=True)
        return {
            "status": "created",
            "id": reminder.id,
            "text": reminder.text,
            "reminder_time": parsed_time.isoformat(),
            "formatted_time": formatted_time,
            "message": f"Reminder set: '{reminder.text}' for {formatted_time}.",
            "verified": True
        }
    except Exception as e:
        logger.error(f"Error saving reminder: {e}")
        return {"status": "error", "error": str(e), "verified": False}
    finally:
        db.close()

@registry.register(
    name="list_reminders",
    description="List all active user-defined reminders.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    permission_level="normal",
    category="reminders"
)
def list_reminders() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        reminders = db.query(Reminder).filter(
            Reminder.is_active == True,
            Reminder.is_completed == False
        ).order_by(Reminder.reminder_time.asc()).all()

        if not reminders:
            return {
                "status": "empty",
                "reminders": [],
                "message": "You have no active reminders.",
                "verified": True
            }

        items = []
        msg_lines = ["Here are your active reminders:"]
        for r in reminders:
            formatted = format_display_time(r.reminder_time, include_date=True)
            items.append({
                "id": r.id,
                "text": r.text,
                "time": formatted,
                "raw_time": r.reminder_time.isoformat()
            })
            msg_lines.append(f"• '{r.text}' at {formatted}")

        return {
            "status": "success",
            "reminders": items,
            "message": "\n".join(msg_lines),
            "verified": True
        }
    finally:
        db.close()

@registry.register(
    name="delete_reminder",
    description="Cancel or delete a reminder by ID or matching description.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The reminder ID or keywords in the reminder to cancel (e.g. 'assignment', 'all', '1')"
            }
        },
        "required": ["query"]
    },
    permission_level="normal",
    category="reminders"
)
def delete_reminder(query: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        q_clean = query.strip().lower()
        if q_clean in ["all", "everything"]:
            count = db.query(Reminder).filter(Reminder.is_active == True).update({Reminder.is_active: False})
            db.commit()
            return {"status": "deleted_all", "message": f"Cancelled all {count} active reminders.", "verified": True}

        # Try by ID
        if q_clean.isdigit():
            r = db.query(Reminder).filter(Reminder.id == int(q_clean)).first()
            if r:
                r.is_active = False
                db.commit()
                return {"status": "deleted", "message": f"Cancelled reminder: '{r.text}'.", "verified": True}

        # Search by text
        reminders = db.query(Reminder).filter(Reminder.is_active == True).all()
        for r in reminders:
            if q_clean in r.text.lower():
                r.is_active = False
                db.commit()
                return {"status": "deleted", "message": f"Cancelled reminder: '{r.text}'.", "verified": True}

        return {"status": "not_found", "message": f"No active reminder found matching '{query}'.", "verified": False}
    finally:
        db.close()
