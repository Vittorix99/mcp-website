from datetime import datetime, timezone
from typing import Dict, List, Optional

from dto import ErrorLogDTO
from models import ErrorLog
from repositories.base import BaseRepository


class ErrorLogRepository(BaseRepository[ErrorLog, ErrorLogDTO]):
    def __init__(self):
        super().__init__("error_logs", ErrorLog, ErrorLogDTO)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_from_dto(self, dto: ErrorLogDTO) -> str:
        model = dto.to_model()
        now = self._now_iso()
        model.created_at = model.created_at or now
        model.updated_at = now
        ref = self.collection.document()
        ref.set(model.to_firestore(include_none=True))
        return ref.id

    def get_dto(self, error_log_id: str) -> Optional[ErrorLogDTO]:
        if not error_log_id:
            return None
        model = self.get_model(error_log_id)
        return ErrorLogDTO.from_model(model) if model else None

    def get_model(self, error_log_id: str) -> Optional[ErrorLog]:
        if not error_log_id:
            return None
        doc = self.collection.document(error_log_id).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def list_dtos(
        self,
        limit: int = 100,
        service: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[ErrorLogDTO]:
        safe_limit = max(1, min(int(limit or 100), 500))
        # Stream + in-memory sort/filter to avoid Firestore index constraints.
        all_rows: List[ErrorLogDTO] = []
        service_normalized = service.strip().lower() if service else None
        for doc in self.collection.limit(500).stream():
            dto = ErrorLogDTO.from_model(self._model_from_snapshot(doc))
            all_rows.append(dto)

        all_rows.sort(key=lambda row: row.created_at or "", reverse=True)

        result: List[ErrorLogDTO] = []
        for dto in all_rows:
            if service_normalized and (dto.service or "").strip().lower() != service_normalized:
                continue
            if resolved is not None and bool(dto.resolved) != bool(resolved):
                continue
            result.append(dto)
            if len(result) >= safe_limit:
                break
        return result

    def update_from_payload(self, error_log_id: str, payload: Dict) -> bool:
        if not error_log_id:
            return False
        updates = dict(payload or {})
        updates.pop("id", None)
        updates["updated_at"] = self._now_iso()
        self.collection.document(error_log_id).set(updates, merge=True)
        return True
