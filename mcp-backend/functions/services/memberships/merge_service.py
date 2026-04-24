import logging
from typing import Dict, List, Optional

from domain.membership_rules import dedupe_renewals_by_year, membership_years_from_renewals
from errors.service_errors import NotFoundError, ValidationError
from interfaces.repositories import MembershipRepositoryProtocol, ParticipantRepositoryProtocol
from interfaces.services import Pass2UServiceProtocol
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.memberships.pass2u_service import Pass2UService


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
        self.pass2u_service = pass2u_service or Pass2UService()

    @staticmethod
    def _unique_sorted(values: List[Optional[str]]) -> List[str]:
        return sorted({value for value in values if value})

    @staticmethod
    def _coerce_years(values: List[object]) -> List[int]:
        years: List[int] = []
        for value in values or []:
            try:
                years.append(int(value))
            except (TypeError, ValueError):
                continue
        return years

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

        # Marca source come in fase di merge immediatamente.
        # Se un acquisto concorrente tenta di rinnovare source durante il merge,
        # il secondo sweep (step 9b) riparerà i riferimenti prima della delete.
        self.membership_repository.set_merging(source_id, True)

        try:
            merged_purchases = self._unique_sorted([
                *(source.purchases or []),
                *(target.purchases or []),
                source.purchase_id,
                target.purchase_id,
            ])
            merged_events = self._unique_sorted([
                *(source.attended_events or []),
                *(target.attended_events or []),
            ])

            merged_renewals = dedupe_renewals_by_year([
                *(target.renewals or []),
                *(source.renewals or []),
            ])
            merged_years = membership_years_from_renewals(
                merged_renewals,
                fallback_start_date=target.start_date or source.start_date,
                fallback_end_date=target.end_date or source.end_date,
            )
            merged_years = sorted({
                *merged_years,
                *self._coerce_years(source.membership_years or []),
                *self._coerce_years(target.membership_years or []),
            })

            # 6. Invalida wallet del source (non bloccante)
            if source.wallet_pass_id:
                try:
                    self.pass2u_service.invalidate_membership_pass(source.wallet_pass_id)
                except Exception as exc:
                    self.logger.warning("Invalidazione source wallet fallita (non bloccante): %s", exc)

            # 7. Sposta riferimenti participant source -> target (primo sweep)
            participants_updated = self.participant_repository.update_membership_reference(source_id, target_id)

            # 8. Aggiorna target con i dati unificati (mantiene contatti del target)
            updates = {
                "name": target.name or source.name,
                "surname": target.surname or source.surname,
                "email": target.email or source.email,
                "phone": target.phone or source.phone,
                "birthdate": target.birthdate or source.birthdate,
                "start_date": target.start_date or source.start_date,
                "end_date": target.end_date or source.end_date,
                "subscription_valid": bool(target.subscription_valid or source.subscription_valid),
                "membership_sent": bool(target.membership_sent or source.membership_sent),
                "membership_type": target.membership_type or source.membership_type,
                "purchase_id": target.purchase_id or source.purchase_id,
                "membership_fee": target.membership_fee if target.membership_fee is not None else source.membership_fee,
                "purchases": merged_purchases,
                "attended_events": merged_events,
                "renewals": merged_renewals,
                "membership_years": merged_years,
            }
            self.membership_repository.update_fields(target_id, updates)
            self.membership_repository.clear_wallet(target_id)

            # 9b. Secondo sweep: cattura partecipanti creati su source_id durante
            # la finestra di merge (tra step 7 e adesso).
            late_refs = self.participant_repository.update_membership_reference(source_id, target_id)
            if late_refs:
                self.logger.info(
                    "Merge second sweep: %d riferimento/i tardivo/i rerouted source=%s → target=%s",
                    late_refs, source_id, target_id,
                )
                participants_updated += late_refs

            # 9. Elimina source
            self.membership_repository.delete(source_id)

        except Exception:
            # Se il merge fallisce, rimuovi il flag merging per lasciare source utilizzabile.
            try:
                self.membership_repository.set_merging(source_id, None)
            except Exception as cleanup_exc:
                self.logger.warning("Impossibile rimuovere il flag merging da source %s: %s", source_id, cleanup_exc)
            raise

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
            self.logger.warning("Creazione wallet target fallita (non bloccante): %s", exc)

        return {
            "message": "Merge completato",
            "source_id": source_id,
            "target_id": target_id,
            "participants_updated": participants_updated,
            "wallet_pass_id": wallet_pass_id,
            "wallet_url": wallet_url,
            "membership_years": merged_years,
        }
