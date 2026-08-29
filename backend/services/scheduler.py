import datetime
import asyncio
import logging
from typing import Callable, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database import SessionLocal
from backend.models import Reminder

logger = logging.getLogger("AEGIS.Scheduler")

class ReminderScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.notification_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        self.notification_callbacks.append(callback)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.add_job(self.check_due_reminders, 'interval', seconds=3)
            self.scheduler.start()
            logger.info("Reminder scheduler started.")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Reminder scheduler stopped.")

    async def check_due_reminders(self):
        """Checks for due reminders against the actual Windows local clock."""
        now = datetime.datetime.now()
        db = SessionLocal()
        try:
            due_reminders = db.query(Reminder).filter(
                Reminder.is_active == True,
                Reminder.is_completed == False,
                Reminder.reminder_time <= now
            ).all()

            for r in due_reminders:
                hour = int(r.reminder_time.strftime("%I"))
                minute = r.reminder_time.strftime("%M")
                ampm = r.reminder_time.strftime("%p")
                time_str = f"{hour}:{minute} {ampm}"

                logger.info(f"Triggering due reminder: '{r.text}' at {time_str}")
                r.is_completed = True
                db.commit()

                # Dispatch to all registered notification callbacks
                for cb in self.notification_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(r.id, r.text, time_str)
                        else:
                            cb(r.id, r.text, time_str)
                    except Exception as e:
                        logger.error(f"Error invoking reminder callback: {e}")
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
        finally:
            db.close()

reminder_scheduler = ReminderScheduler()
