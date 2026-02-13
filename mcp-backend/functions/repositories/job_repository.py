from typing import Any, Dict, Optional, Union

from config.firebase_config import db
from dto import JobDTO
from models import Job


class JobRepository:
    def __init__(self) -> None:
        self.collection = db.collection("jobs")

    def create(self, payload: Union[Dict[str, Any], JobDTO, Job]) -> str:
        doc_ref = self.collection.document()
        if hasattr(payload, "to_payload"):
            data = payload.to_payload()
        elif hasattr(payload, "to_firestore"):
            data = payload.to_firestore(include_none=True)
        else:
            data = payload
        doc_ref.set(data)
        return doc_ref.id

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        snap = self.collection.document(job_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        data["id"] = job_id
        return data

    def get_model(self, job_id: str) -> Optional[Job]:
        snap = self.collection.document(job_id).get()
        if not snap.exists:
            return None
        return Job.from_firestore(snap.to_dict() or {}, job_id)

    def get_dto(self, job_id: str) -> Optional[JobDTO]:
        model = self.get_model(job_id)
        if not model:
            return None
        return JobDTO.from_model(model)

    def update(self, job_id: str, payload: Union[Dict[str, Any], JobDTO, Job]) -> None:
        if hasattr(payload, "to_update_payload"):
            data = payload.to_update_payload()  # type: ignore[attr-defined]
        elif hasattr(payload, "to_payload"):
            data = payload.to_payload()
        elif hasattr(payload, "to_firestore"):
            data = payload.to_firestore(include_none=True)
        else:
            data = payload
        self.collection.document(job_id).update(data)

    def create_from_model(self, job: Job) -> str:
        return self.create(job)

    def update_from_model(self, job_id: str, payload: Union[JobDTO, Job]) -> None:
        self.update(job_id, payload)

    def set(self, job_id: str, payload: Dict[str, Any], merge: bool = True) -> None:
        self.collection.document(job_id).set(payload, merge=merge)
