import logging
from typing import Dict, Any, List, Optional
from backend.database import SessionLocal
from backend.models import Memory

logger = logging.getLogger("AEGIS.Memory")

class MemoryStore:
    def set_memory(self, key: str, value: str, category: str = "preference") -> Dict[str, Any]:
        clean_key = key.strip().lower()
        db = SessionLocal()
        try:
            mem = db.query(Memory).filter(Memory.key == clean_key).first()
            if mem:
                mem.value = value
                mem.category = category
            else:
                mem = Memory(key=clean_key, value=value, category=category)
                db.add(mem)
            db.commit()
            db.refresh(mem)
            return {"status": "saved", "key": clean_key, "value": value}
        finally:
            db.close()

    def get_memory(self, key: str) -> Optional[str]:
        clean_key = key.strip().lower()
        db = SessionLocal()
        try:
            mem = db.query(Memory).filter(Memory.key == clean_key).first()
            return mem.value if mem else None
        finally:
            db.close()

    def get_all_memories(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            mems = db.query(Memory).order_by(Memory.created_at.desc()).all()
            return [{"id": m.id, "key": m.key, "value": m.value, "category": m.category} for m in mems]
        finally:
            db.close()

    def delete_memory(self, memory_id: int) -> bool:
        db = SessionLocal()
        try:
            mem = db.query(Memory).filter(Memory.id == memory_id).first()
            if mem:
                db.delete(mem)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def clear_memories(self) -> int:
        db = SessionLocal()
        try:
            count = db.query(Memory).delete()
            db.commit()
            return count
        finally:
            db.close()

memory_store = MemoryStore()
