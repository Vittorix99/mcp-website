import logging
from typing import Optional

from config.external_services import PASS2U_API_KEY
from config.firebase_config import db
from models import Membership, MembershipPass, MembershipPassResult
from routes.pass2u_routes import Pass2URoutes
from utils.events_utils import to_iso8601_datetime


class Pass2UService:
    def _get_model_id(self) -> str:
        """
        Legge il model_id attivo da Firestore:
          membership_settings/current_model → model_id (string)
        Va settato dal frontend quando si cambia modello Pass2U.
        """
        doc = db.collection("membership_settings").document("current_model").get()
        if not doc.exists:
            raise RuntimeError("Documento membership_settings/current_model non trovato in Firestore")
        model_id = doc.to_dict().get("model_id")
        if not model_id:
            raise RuntimeError("Campo model_id mancante in membership_settings/current_model")
        return str(model_id)

    def create_membership_pass(
        self,
        membership_id: str,
        membership: Membership,
    ) -> Optional[MembershipPassResult]:
        """
        Crea una tessera wallet su Pass2U.
        Restituisce un MembershipPassResult oppure None se fallisce.
        Non solleva mai eccezioni verso l'esterno.
        """
        try:
            model_id = self._get_model_id()
            api_key = PASS2U_API_KEY
            if not api_key:
                raise RuntimeError("PASS2U_API_KEY non configurata")

            # expirationDate e validity (field DateTime nel model) devono essere ISO 8601.
            expiration_date = to_iso8601_datetime(membership.end_date)
            validity_value = expiration_date or (membership.end_date or "")
            membership_pass = MembershipPass.from_membership(
                membership_id=membership_id,
                membership=membership,
                validity=validity_value,
            )
            payload = membership_pass.to_pass2u_payload(expiration_date=expiration_date)
            result = Pass2URoutes.create_pass(
                model_id=model_id,
                api_key=api_key,
                body=payload,
            )

            if result.status_code == 409:
                # Pass già esistente per questo membership_id — non è un errore
                logging.warning(f"[Pass2U] Pass già esistente per membership {membership_id}")
                return None

            if not result.ok:
                logging.error(
                    "[Pass2U] HTTP %s on create pass (membership=%s, model=%s). Response=%s Payload=%s",
                    result.status_code,
                    membership_id,
                    model_id,
                    result.error_message or result.payload,
                    payload,
                )
                return None

            data = result.payload if isinstance(result.payload, dict) else {}
            pass_id = data.get("passId")
            if not pass_id:
                logging.error(
                    "[Pass2U] Missing passId in success response (membership=%s, model=%s). Payload=%s",
                    membership_id,
                    model_id,
                    result.payload,
                )
                return None

            return MembershipPassResult.from_pass_id(pass_id)

        except Exception as e:
            logging.error(f"[Pass2U] create_membership_pass failed for {membership_id}: {e}")
            return None

    def invalidate_membership_pass(self, pass_id: str) -> bool:
        """
        Invalida una tessera wallet su Pass2U (DELETE pass).
        Restituisce True se invalidata con successo, False altrimenti.
        Non solleva mai eccezioni verso l'esterno.
        """
        try:
            api_key = PASS2U_API_KEY
            if not api_key:
                raise RuntimeError("PASS2U_API_KEY non configurata")
            result = Pass2URoutes.invalidate_pass(
                pass_id=pass_id,
                api_key=api_key,
            )

            if result.status_code == 404:
                logging.warning(f"[Pass2U] Pass {pass_id} non trovato (già eliminato?)")
                return True  # consideriamo ok se non esiste più

            if not result.ok:
                logging.error(
                    "[Pass2U] invalidate failed for %s (status=%s): %s",
                    pass_id,
                    result.status_code,
                    result.error_message or result.payload,
                )
                return False

            logging.info(f"[Pass2U] Pass {pass_id} invalidato con successo")
            return True

        except Exception as e:
            logging.error(f"[Pass2U] invalidate_membership_pass failed for {pass_id}: {e}")
            return False
