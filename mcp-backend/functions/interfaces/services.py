from __future__ import annotations

from typing import Any, Dict, Protocol


class DocumentsServiceProtocol(Protocol):
    storage: Any

    def create_membership_card(self, membership_id: str, membership_data: Any) -> Any:
        ...

    def create_ticket_document(self, ticket_data: Any, event_data: Dict[str, Any], storage_path: str) -> Any:
        ...


class TicketServiceProtocol(Protocol):
    def process_new_ticket(self, participant_id: str, participant_data: Any, send: bool = True) -> Dict[str, Any]:
        ...


class Pass2UServiceProtocol(Protocol):
    def create_membership_pass(self, membership_id: str, membership: Any) -> Any:
        ...

    def invalidate_membership_pass(self, pass_id: str) -> bool:
        ...


class MembershipsServiceProtocol(Protocol):
    def send_card(self, membership_id: str) -> Dict[str, Any]:
        ...
