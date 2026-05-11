import logging
import time

import firebase_admin.auth as fb_auth
from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from config.firebase_config import db
from utils.http_responses import handle_pydantic_error, handle_service_error
from utils.safe_logging import mask_email, redact_sensitive

logger = logging.getLogger("MembersAuthAPI")

_BATCH_SIZE = 50
_BATCH_PAUSE = 1.0


def _write_uid(membership_ref, uid: str) -> None:
    membership_ref.update({"uid": uid})


@admin_endpoint(methods=("POST",))
def provision_member_accounts(req):
    """Batch-provision Firebase Auth accounts for all members without a uid."""
    provisioned = 0
    already_existing = 0
    skipped_no_email = 0
    errors = 0

    docs = list(db.collection("memberships").stream())
    batch = []
    for doc in docs:
        data = doc.to_dict() or {}
        if data.get("uid"):
            continue
        email = (data.get("email") or "").strip()
        if not email:
            skipped_no_email += 1
            continue
        batch.append((doc.reference, email))

    for i in range(0, len(batch), _BATCH_SIZE):
        chunk = batch[i : i + _BATCH_SIZE]
        for ref, email in chunk:
            try:
                user = fb_auth.create_user(email=email, email_verified=False)
                _write_uid(ref, user.uid)
                provisioned += 1
                logger.info("provision_member_accounts: created uid for %s", mask_email(email))
            except fb_auth.EmailAlreadyExistsError:
                try:
                    existing = fb_auth.get_user_by_email(email)
                    _write_uid(ref, existing.uid)
                    already_existing += 1
                    logger.info("provision_member_accounts: reused uid for %s", mask_email(email))
                except Exception as exc:
                    logger.error(
                        "provision_member_accounts: get_user_by_email failed for %s: %s",
                        mask_email(email),
                        redact_sensitive(str(exc)),
                    )
                    errors += 1
            except Exception as exc:
                logger.error(
                    "provision_member_accounts: create_user failed for %s: %s",
                    mask_email(email),
                    redact_sensitive(str(exc)),
                )
                errors += 1

        if i + _BATCH_SIZE < len(batch):
            time.sleep(_BATCH_PAUSE)

    return jsonify(
        {
            "provisioned": provisioned,
            "already_existing": already_existing,
            "skipped_no_email": skipped_no_email,
            "errors": errors,
        }
    ), 200


@admin_endpoint(methods=("POST",))
def provision_single_member_account(req):
    """Provision a Firebase Auth account for a single member by membership_id."""
    body = req.get_json(silent=True) or {}
    membership_id = (body.get("membership_id") or "").strip()
    if not membership_id:
        return jsonify({"error": "membership_id is required"}), 400

    doc = db.collection("memberships").document(membership_id).get()
    if not doc.exists:
        return jsonify({"error": "Membership not found"}), 404

    data = doc.to_dict() or {}
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify({"uid": None, "status": "error", "message": "No email on membership"}), 400

    try:
        user = fb_auth.create_user(email=email, email_verified=False)
        _write_uid(doc.reference, user.uid)
        logger.info("provision_single_member_account: created uid for %s", mask_email(email))
        return jsonify({"uid": user.uid, "status": "created", "message": "Account created"}), 200
    except fb_auth.EmailAlreadyExistsError:
        try:
            existing = fb_auth.get_user_by_email(email)
            _write_uid(doc.reference, existing.uid)
            logger.info("provision_single_member_account: reused uid for %s", mask_email(email))
            return jsonify({"uid": existing.uid, "status": "existing", "message": "Account already existed"}), 200
        except Exception as exc:
            logger.error(
                "provision_single_member_account: get_user_by_email failed for %s: %s",
                mask_email(email),
                redact_sensitive(str(exc)),
            )
            return jsonify({"uid": None, "status": "error", "message": str(exc)}), 500
    except Exception as exc:
        logger.error(
            "provision_single_member_account: create_user failed for %s: %s",
            mask_email(email),
            redact_sensitive(str(exc)),
        )
        return jsonify({"uid": None, "status": "error", "message": str(exc)}), 500
