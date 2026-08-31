import datetime
import logging
from typing import Dict, Any, List, Optional
from backend.database import SessionLocal
from backend.models import Routine
from backend.config import settings

logger = logging.getLogger("AEGIS.RoutineLearner")

class RoutineLearner:
    def log_action(self, action_type: str, target: str):
        """Logs user computer action to discover frequent daily workflows (if learning enabled)."""
        if not settings.LEARNING_ENABLED:
            return

        now = datetime.datetime.now()
        hour = now.hour
        time_slot = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 22 else "night"

        db = SessionLocal()
        try:
            routine = db.query(Routine).filter(
                Routine.action_type == action_type,
                Routine.target == target,
                Routine.time_of_day == time_slot
            ).first()

            if routine:
                routine.frequency += 1
                routine.last_executed = now
            else:
                routine = Routine(
                    action_type=action_type,
                    target=target,
                    time_of_day=time_slot,
                    frequency=1,
                    last_executed=now,
                    auto_enabled=False
                )
                db.add(routine)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging routine: {e}")
        finally:
            db.close()

    def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """Returns non-intrusive proactive suggestions based on high-frequency habits."""
        if not settings.LEARNING_ENABLED:
            return []

        now = datetime.datetime.now()
        hour = now.hour
        time_slot = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 22 else "night"

        db = SessionLocal()
        try:
            # Routines with at least 3 occurrences during this time slot
            candidates = db.query(Routine).filter(
                Routine.time_of_day == time_slot,
                Routine.frequency >= 3
            ).order_by(Routine.frequency.desc()).limit(3).all()

            suggestions = []
            for c in candidates:
                suggestions.append({
                    "id": c.id,
                    "action_type": c.action_type,
                    "target": c.target,
                    "time_slot": c.time_of_day,
                    "frequency": c.frequency,
                    "message": f"You usually open {c.target} around this time. Would you like me to open it?"
                })
            return suggestions
        finally:
            db.close()

    def get_all_routines(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            routines = db.query(Routine).order_by(Routine.frequency.desc()).all()
            return [
                {
                    "id": r.id,
                    "action_type": r.action_type,
                    "target": r.target,
                    "time_of_day": r.time_of_day,
                    "frequency": r.frequency,
                    "auto_enabled": r.auto_enabled
                }
                for r in routines
            ]
        finally:
            db.close()

    def delete_routine(self, routine_id: int) -> bool:
        db = SessionLocal()
        try:
            r = db.query(Routine).filter(Routine.id == routine_id).first()
            if r:
                db.delete(r)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def clear_all_routines(self) -> int:
        db = SessionLocal()
        try:
            count = db.query(Routine).delete()
            db.commit()
            return count
        finally:
            db.close()

routine_learner = RoutineLearner()
