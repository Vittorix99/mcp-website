import logging

from firebase_functions import scheduler_fn
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db

logger = logging.getLogger("new_year_trigger")

# Firestore batch limit
_BATCH_SIZE = 500


@scheduler_fn.on_schedule(schedule="0 0 1 1 *", timezone="Europe/Rome")
def invalidate_memberships_new_year(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Runs at 00:00 on January 1st (Europe/Rome).
    Imposta subscription_valid=False su tutte le tessere attive,
    così i QR dell'anno precedente non sono più accettati allo scanner.
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
