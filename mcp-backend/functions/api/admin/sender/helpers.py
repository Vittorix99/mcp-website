from typing import Optional

from services.sender.sender_service import SenderService

_sender_service: Optional[SenderService] = None


def get_sender_service() -> SenderService:
    global _sender_service
    if _sender_service is None:
        _sender_service = SenderService()
    return _sender_service
