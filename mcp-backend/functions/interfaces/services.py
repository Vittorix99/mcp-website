from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Protocol

if TYPE_CHECKING:
    from dto.event_api import (
        AdminEventEnvelopeResponseDTO,
        AdminEventResponseDTO,
        CreateEventRequestDTO,
        EventActionResponseDTO,
        PublicEventResponseDTO,
        UpdateEventRequestDTO,
    )
    from dto.admin import (
        AdminActionResponseDTO,
        AdminListResponseDTO,
        AdminResponseDTO,
        CreateAdminRequestDTO,
        UpdateAdminRequestDTO,
    )
    from dto.membership_api import (
        CreateMembershipRequestDTO,
        MembershipActionResponseDTO,
        MembershipPriceResponseDTO,
        MembershipResponseDTO,
        MembershipWalletPassResponseDTO,
        RenewMembershipRequestDTO,
        UpdateMembershipRequestDTO,
        WalletModelResponseDTO,
    )
    from dto.participant_api import (
        CheckParticipantsResponseDTO,
        CheckoutParticipantRequestDTO,
        LocationActionResponseDTO,
        LocationBulkActionResponseDTO,
        LocationJobResponseDTO,
        ParticipantActionResponseDTO,
        ParticipantCreateRequestDTO,
        ParticipantResponseDTO,
        ParticipantUpdateRequestDTO,
        SendLocationRequestDTO,
        SendLocationToAllRequestDTO,
        SendOmaggioEmailsRequestDTO,
        SendOmaggioEmailsResponseDTO,
    )
    from dto.preorder import (
        EventOrderCreateResponseDTO,
        OrderCaptureDTO,
        OrderCaptureResponseDTO,
        PreOrderDTO,
    )
    from dto.purchase import (
        CreatePurchaseRequestDTO,
        PurchaseActionResponseDTO,
        PurchaseDTO,
    )
    from dto.newsletter_api import (
        NewsletterActionResponseDTO,
        NewsletterConsentsListResponseDTO,
        NewsletterParticipantsRequestDTO,
        NewsletterSignupEnvelopeResponseDTO,
        NewsletterSignupRequestDTO,
        NewsletterSignupsListResponseDTO,
        NewsletterUpdateRequestDTO,
    )
    from dto.entrance_api import (
        DeactivateScanTokenRequestDTO,
        DeactivateScanTokenResponseDTO,
        GenerateScanTokenRequestDTO,
        GenerateScanTokenResponseDTO,
        ManualEntryRequestDTO,
        ManualEntryResponseDTO,
        ValidateEntryRequestDTO,
        ValidateEntryResponseDTO,
        VerifyScanTokenQueryDTO,
        VerifyScanTokenResponseDTO,
    )
    from models import Event


class AdminServiceProtocol(Protocol):
    def create(self, dto: CreateAdminRequestDTO, created_by: str) -> AdminActionResponseDTO:
        ...

    def get_all(self) -> AdminListResponseDTO:
        ...

    def get_by_id(self, admin_id: str) -> AdminResponseDTO:
        ...

    def update(self, dto: UpdateAdminRequestDTO) -> AdminActionResponseDTO:
        ...

    def delete(self, admin_id: str) -> AdminActionResponseDTO:
        ...


class EventsServiceProtocol(Protocol):
    def create_event(self, dto: CreateEventRequestDTO, admin_uid: str) -> EventActionResponseDTO:
        ...

    def update_event(self, dto: UpdateEventRequestDTO, admin_uid: str) -> EventActionResponseDTO:
        ...

    def delete_event(self, event_id: str, admin_uid: str) -> EventActionResponseDTO:
        ...

    def get_all_events(self) -> list[AdminEventResponseDTO]:
        ...

    def get_event_by_id(
        self,
        event_id: str | None = None,
        slug: str | None = None,
    ) -> AdminEventEnvelopeResponseDTO:
        ...
    
    def list_public_events(self, view: str | None = None) -> list[PublicEventResponseDTO]:
        ...

    def list_upcoming_events(self, limit: int = 5) -> list[PublicEventResponseDTO]:
        ...

    def get_next_public_event(self) -> list[PublicEventResponseDTO]:
        ...

    def get_public_event_by_id(
        self,
        event_id: str | None = None,
        slug: str | None = None,
    ) -> PublicEventResponseDTO:
        ...


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
    def get_all(self, year: int | None = None) -> list[MembershipResponseDTO]:
        ...

    def get_by_id(self, membership_id: str | None, slug: str | None = None) -> MembershipResponseDTO:
        ...

    def create(self, dto: CreateMembershipRequestDTO) -> MembershipActionResponseDTO:
        ...

    def update(self, membership_id: str, dto: UpdateMembershipRequestDTO) -> MembershipActionResponseDTO:
        ...

    def renew(self, membership_id: str, dto: RenewMembershipRequestDTO) -> MembershipActionResponseDTO:
        ...

    def delete(self, membership_id: str) -> MembershipActionResponseDTO:
        ...

    def send_card(self, membership_id: str) -> MembershipActionResponseDTO:
        ...

    def create_wallet_pass(self, membership_id: str) -> MembershipWalletPassResponseDTO:
        ...

    def invalidate_wallet_pass(self, membership_id: str) -> MembershipActionResponseDTO:
        ...

    def get_membership_price(self, year: int | None = None) -> MembershipPriceResponseDTO:
        ...

    def set_membership_price(self, price: float, year: int | None = None) -> MembershipPriceResponseDTO:
        ...

    def get_wallet_model(self) -> WalletModelResponseDTO:
        ...

    def set_wallet_model(self, model_id: str) -> WalletModelResponseDTO:
        ...


class ParticipantsServiceProtocol(Protocol):
    def get_all(self, event_id: str) -> list[ParticipantResponseDTO]:
        ...

    def get_by_id(self, event_id: str, participant_id: str) -> ParticipantResponseDTO:
        ...

    def create(self, dto: ParticipantCreateRequestDTO) -> ParticipantActionResponseDTO:
        ...

    def update(self, event_id: str, participant_id: str, dto: ParticipantUpdateRequestDTO) -> ParticipantActionResponseDTO:
        ...

    def delete(self, event_id: str, participant_id: str) -> ParticipantActionResponseDTO:
        ...

    def send_ticket(self, event_id: str, participant_id: str) -> ParticipantActionResponseDTO:
        ...

    def send_omaggio_emails(
        self,
        dto: SendOmaggioEmailsRequestDTO,
    ) -> SendOmaggioEmailsResponseDTO:
        ...

    def check_participants(
        self,
        event_id: str,
        participants: list[CheckoutParticipantRequestDTO],
    ) -> CheckParticipantsResponseDTO:
        ...


class LocationServiceProtocol(Protocol):
    def send_location(self, dto: SendLocationRequestDTO) -> LocationActionResponseDTO:
        ...

    def start_send_location_job(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationJobResponseDTO:
        ...

    def send_location_to_all(
        self,
        dto: SendLocationToAllRequestDTO,
    ) -> LocationBulkActionResponseDTO:
        ...


class EventPaymentServiceProtocol(Protocol):
    def create_order_event(
        self,
        payload: PreOrderDTO,
        event_data: Event | None = None,
    ) -> EventOrderCreateResponseDTO:
        ...

    def capture_order_event(
        self,
        payload: OrderCaptureDTO,
    ) -> OrderCaptureResponseDTO:
        ...


class PurchasesServiceProtocol(Protocol):
    def get_all(self) -> list[PurchaseDTO]:
        ...

    def get_by_id(
        self,
        purchase_id: str | None,
        slug: str | None = None,
    ) -> PurchaseDTO:
        ...

    def create(self, dto: CreatePurchaseRequestDTO) -> PurchaseActionResponseDTO:
        ...

    def delete(self, purchase_id: str) -> PurchaseActionResponseDTO:
        ...


class NewsletterServiceProtocol(Protocol):
    def signup(self, dto: NewsletterSignupRequestDTO) -> NewsletterActionResponseDTO:
        ...

    def get_signup_by_id(self, signup_id: str) -> NewsletterSignupEnvelopeResponseDTO:
        ...

    def get_all_signups(self) -> NewsletterSignupsListResponseDTO:
        ...

    def get_all_consents(self) -> NewsletterConsentsListResponseDTO:
        ...

    def update_signup(self, dto: NewsletterUpdateRequestDTO) -> NewsletterActionResponseDTO:
        ...

    def delete_signup(self, signup_id: str) -> NewsletterActionResponseDTO:
        ...

    def add_participants(self, dto: NewsletterParticipantsRequestDTO) -> NewsletterActionResponseDTO:
        ...


class EntranceServiceProtocol(Protocol):
    def generate_scan_token(
        self, dto: GenerateScanTokenRequestDTO, admin_uid: str
    ) -> GenerateScanTokenResponseDTO:
        ...

    def verify_scan_token(self, dto: VerifyScanTokenQueryDTO) -> VerifyScanTokenResponseDTO:
        ...

    def validate_entry(self, dto: ValidateEntryRequestDTO) -> ValidateEntryResponseDTO:
        ...

    def manual_entry(
        self, dto: ManualEntryRequestDTO, admin_uid: str
    ) -> ManualEntryResponseDTO:
        ...

    def deactivate_scan_token(
        self, dto: DeactivateScanTokenRequestDTO, admin_uid: str
    ) -> DeactivateScanTokenResponseDTO:
        ...
