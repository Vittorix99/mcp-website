import logging
from typing import Dict, Optional

from errors.service_errors import NotFoundError, ValidationError
from interfaces.repositories import MembershipRepositoryProtocol, ParticipantRepositoryProtocol
from interfaces.services import Pass2UServiceProtocol
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.memberships.pass2u_service import build_pass2u_service
from utils.safe_logging import redact_sensitive


class MergeService:
    def __init__(
        self,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        pass2u_service: Optional[Pass2UServiceProtocol] = None,
    ):
        self.logger = logging.getLogger("MergeService")
        self.membership_repository = membership_repository or MembershipRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        self._pass2u_service = pass2u_service

    @property
    def pass2u_service(self):
        if self._pass2u_service is None:
            self._pass2u_service = build_pass2u_service()
        return self._pass2u_service

    @pass2u_service.setter
    def pass2u_service(self, service):
        self._pass2u_service = service

    def merge(self, source_id: str, target_id: str) -> Dict[str, object]:
        source_id = (source_id or "").strip()
        target_id = (target_id or "").strip()

        if not source_id or not target_id:
            raise ValidationError("source_id e target_id sono obbligatori")
        if source_id == target_id:
            raise ValidationError("source_id e target_id devono essere diversi")

        source = self.membership_repository.get(source_id)
        if not source:
            raise NotFoundError("Membership sorgente non trovata")
        target = self.membership_repository.get(target_id)
        if not target:
            raise NotFoundError("Membership destinazione non trovata")

        result = self.membership_repository.merge_atomic(source_id, target_id)
        participants_updated = result['participants_updated']
        merged_years = result['membership_years']
        # Provider effects follow the atomic database commit, never a rejected merge.
        for pass_id in set(result['old_wallet_ids']):
            try:
                self.pass2u_service.invalidate_membership_pass(pass_id)
            except Exception as exc:
                self.logger.warning("Invalidazione wallet fallita (non bloccante): %s", redact_sensitive(str(exc)))

        # 10. Crea nuovo wallet per target (non bloccante)
        wallet_pass_id = None
        wallet_url = None
        try:
            refreshed_target = self.membership_repository.get(target_id)
            wallet = self.pass2u_service.create_membership_pass(target_id, refreshed_target)
            if wallet:
                wallet_pass_id = wallet.pass_id
                wallet_url = wallet.wallet_url
                self.membership_repository.set_wallet(target_id, wallet_pass_id, wallet_url)
        except Exception as exc:
            self.logger.warning("Creazione wallet target fallita (non bloccante): %s", redact_sensitive(str(exc)))

        return {
            "message": "Merge completato",
            "source_id": source_id,
            "target_id": target_id,
            "participants_updated": participants_updated,
            "wallet_pass_id": wallet_pass_id,
            "wallet_url": wallet_url,
            "membership_years": merged_years,
        }
