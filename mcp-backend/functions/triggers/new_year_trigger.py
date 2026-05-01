import logging

from firebase_functions import scheduler_fn
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db

logger = logging.getLogger("new_year_trigger")

# Limite operativo di Firestore: massimo 500 write per batch.
_BATCH_SIZE = 500


@scheduler_fn.on_schedule(schedule="0 0 1 1 *", timezone="Europe/Rome")
def invalidate_memberships_new_year(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Gira ogni 1 gennaio a mezzanotte.
    Invalida le tessere attive: da quel momento lo scanner rifiuta i QR dell'anno precedente.
    """
    logger.info("invalidate_memberships_new_year: avvio invalidazione tessere")

    docs = (
        db.collection("memberships")
        .where(filter=FieldFilter("subscription_valid", "==", True))
        .stream()
    )

    batch = db.batch()
    count = 0
    total = 0

    for doc in docs:
        # Non cancelliamo la membership: la rendiamo non valida finche' non viene rinnovata.
        batch.update(doc.reference, {"subscription_valid": False})
        count += 1
        total += 1

        if count == _BATCH_SIZE:
            batch.commit()
            logger.info("invalidate_memberships_new_year: commit batch (%d tessere)", total)
            batch = db.batch()
            count = 0

    if count > 0:
        batch.commit()

    logger.info(
        "invalidate_memberships_new_year: completato — %d tessere invalidate", total
    )
