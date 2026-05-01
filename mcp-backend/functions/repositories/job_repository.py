from typing import Any, Dict, Optional

from models import Job
from repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self) -> None:
        super().__init__("jobs", Job)

    def create_from_model(self, job: Job) -> str:
        doc_ref = self.collection.document()
        doc_ref.set(job.to_firestore(include_none=True))
        return doc_ref.id

    def get_model(self, job_id: str) -> Optional[Job]:
        return self.get_by_id(job_id)

    def update(self, job_id: str, payload: Dict[str, Any]) -> None:
        self.collection.document(job_id).update(payload)

    def update_from_model(self, job_id: str, job: Job) -> None:
        self.collection.document(job_id).update(job.to_firestore(include_none=False))

    def set(self, job_id: str, payload: Dict[str, Any], merge: bool = True) -> None:
        self.collection.document(job_id).set(payload, merge=merge)
