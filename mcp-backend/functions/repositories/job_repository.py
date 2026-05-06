from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple, Type

from google.cloud.firestore_v1 import FieldFilter
from google.cloud.firestore_v1 import transactional as _fs_transactional

from config.firebase_config import db
from models import AnalyticsJob, Job, LocationJob
from repositories.base import BaseRepository


JOBS_COLLECTION = "jobs"
LOCATION_JOBS_COLLECTION = "location_jobs"
ANALYTICS_JOBS_COLLECTION = "analytics_jobs"


@_fs_transactional
def _claim_queued_tx(transaction, job_ref):
    snap = job_ref.get(transaction=transaction)
    if not snap.exists:
        return False
    payload = snap.to_dict() or {}
    if payload.get("status") != "queued":
        return False
    transaction.update(
        job_ref,
        {
            "status": "running",
            "started_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    )
    return True


class JobRepository(BaseRepository[Job]):
    def __init__(self, collection_name: str = JOBS_COLLECTION, model_cls: Type[Job] = Job) -> None:
        super().__init__(collection_name, model_cls)

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

    def get_raw(self, job_id: str) -> Optional[Dict[str, Any]]:
        snap = self.collection.document(job_id).get()
        if not snap.exists:
            return None
        payload = snap.to_dict() or {}
        payload["id"] = snap.id
        return payload

    def stream_raw_by_type(self, job_type: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
        snaps = self.collection.where(filter=FieldFilter("type", "==", job_type)).stream()
        for snap in snaps:
            yield snap.id, (snap.to_dict() or {})

    def claim_queued(self, job_id: str) -> bool:
        job_ref = self.collection.document(job_id)
        return _claim_queued_tx(db.transaction(), job_ref)


class LocationJobRepository(JobRepository):
    def __init__(self) -> None:
        super().__init__(LOCATION_JOBS_COLLECTION, LocationJob)


class AnalyticsJobRepository(JobRepository):
    def __init__(self) -> None:
        super().__init__(ANALYTICS_JOBS_COLLECTION, AnalyticsJob)
