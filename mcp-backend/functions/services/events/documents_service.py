import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, Optional

from config.firebase_config import bucket
from utils.pdf_template import generate_membership_pdf, generate_ticket_pdf


DEFAULT_MEMBERSHIP_LOGO_PATH = "logos/logo_white.png"
DEFAULT_MEMBERSHIP_PATTERN_PATH = "patterns/FINAL MCP PATTERN - ORANGE.png"
DEFAULT_TICKET_LOGO_PATH = "logos/logo_white.png"


@dataclass
class StoredDocument:
    storage_path: str
    public_url: str
    buffer: Optional[BytesIO] = None


class DocumentsService:
    def __init__(self, storage=bucket):
        self.storage = storage
        self.logger = logging.getLogger("DocumentsService")

    def _normalize_payload(self, data: Any) -> Dict[str, Any]:
        if hasattr(data, "to_payload"):
            return data.to_payload()
        if isinstance(data, dict):
            return dict(data)
        raise ValueError("data must be a dict or a DTO with to_payload()")

    def _store_pdf(self, storage_path: str, pdf_buffer: BytesIO) -> StoredDocument:
        if not pdf_buffer:
            raise ValueError("pdf_buffer is required")
        pdf_buffer.seek(0)
        blob = self.storage.blob(storage_path)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_buffer.seek(0)
        return StoredDocument(storage_path=storage_path, public_url=blob.public_url, buffer=pdf_buffer)

    def create_membership_card(self, membership_id: str, membership_data: Any) -> StoredDocument:
        """
        Legacy helper kept for backward compatibility with existing flows/tests.
        Wallet pass is the primary flow, but PDF generation is still supported.
        """
        payload = self._normalize_payload(membership_data)
        payload["membership_id"] = membership_id

        if payload.get("subscription_valid") is False:
            raise ValueError("Subscription not valid")

        pdf_buffer = generate_membership_pdf(
            payload,
            DEFAULT_MEMBERSHIP_LOGO_PATH,
            DEFAULT_MEMBERSHIP_PATTERN_PATH,
        )
        if not pdf_buffer:
            raise RuntimeError("PDF generation failed")

        storage_path = f"memberships/cards/{membership_id}.pdf"
        return self._store_pdf(storage_path, pdf_buffer)

    def create_ticket_document(
        self,
        ticket_data: Any,
        event_data: Dict[str, Any],
        storage_path: str,
        logo_path: Optional[str] = None,
    ) -> StoredDocument:
        payload = self._normalize_payload(ticket_data)
        pdf_buffer = generate_ticket_pdf(
            payload,
            event_data,
            logo_path or DEFAULT_TICKET_LOGO_PATH,
        )
        if not pdf_buffer:
            raise RuntimeError("PDF generation failed")
        return self._store_pdf(storage_path, pdf_buffer)
