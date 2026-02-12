import logging
from typing import Any, Dict, Optional

MAILERLITE_GROUP_NEWSLETTER = "newsletter"
MAILERLITE_GROUP_MEMBERSHIPS = "memberships"
from utils.events_utils import normalize_email

from .client import MailerLiteClient, MailerLiteError, filter_kwargs
from .groups_client import GroupsClient
from .subscribers_registry import MailerLiteSubscribersRegistry

logger = logging.getLogger("MailerLiteSubscribersClient")

DEFAULT_FIELDS = {
    "name",
    "last_name",
    "phone",
    "company",
    "city",
    "country",
    "state",
    "z_i_p",
}

CUSTOM_FIELDS = {
    "birthdate",
    "gender",
    "membership_id",
    "participant_id",
}

ALLOWED_FIELDS = DEFAULT_FIELDS | CUSTOM_FIELDS


class SubscribersClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()
        self.groups_client = GroupsClient(self.client)
        self.registry = MailerLiteSubscribersRegistry()
        self._group_cache: Dict[str, int] = {}

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "cursor", "filter"})
        return self.client.call(self.client.sdk.subscribers.list, **kwargs)

    def _to_int(self, value: Any, label: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be int-compatible, got {value!r}")

    def create(self, email: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        fields = payload.get("fields") if payload else None
        self._validate_fields(fields)
        kwargs = filter_kwargs(
            payload,
            {
                "fields",
                "groups",
                "status",
                "subscribed_at",
                "opted_in_at",
                "unsubscribed_at",
                "resubscribe",
                "ip_address",
                "optin_ip",
            },
        )
        normalized = normalize_email(email)
        create_email = normalized or email
        response = self.client.call(self.client.sdk.subscribers.create, create_email, **kwargs)
        try:
            subscriber_id = self._extract_id(response)
            if subscriber_id and normalized:
                self.registry.upsert(normalized, str(subscriber_id))
        except Exception as e:
            logger.warning("Unable to store MailerLite subscriber %s: %s", email, e)
        return response

    def update(self, email: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        fields = payload.get("fields") if payload else None
        self._validate_fields(fields)
        kwargs = filter_kwargs(
            payload,
            {
                "fields",
                "groups",
                "status",
                "subscribed_at",
                "opted_in_at",
                "unsubscribed_at",
                "resubscribe",
                "ip_address",
                "optin_ip",
            },
        )
        return self.client.call(self.client.sdk.subscribers.update, email, **kwargs)

    def get(self, email: str) -> Any:
        return self.client.call(self.client.sdk.subscribers.get, email)

    def delete_subscriber(self, subscriber_id: str) -> Any:
        subscriber_id = self._to_int(subscriber_id, "subscriber_id")
        response = self.client.call(self.client.sdk.subscribers.delete, subscriber_id)
        try:
            self.registry.delete_by_mailerlite_id(subscriber_id)
        except Exception as e:
            logger.warning("Unable to remove registry entry for %s: %s", subscriber_id, e)
        if isinstance(response, int):
            return {"status": response}
        return response

    def forget_subscriber(self, subscriber_id: str) -> Any:
        subscriber_id = self._to_int(subscriber_id, "subscriber_id")
        response = self.client.call(self.client.sdk.subscribers.forget, subscriber_id)
        try:
            self.registry.delete_by_mailerlite_id(subscriber_id)
        except Exception as e:
            logger.warning("Unable to remove registry entry for %s: %s", subscriber_id, e)
        if isinstance(response, int):
            return {"status": response}
        return response

    def _compact_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in fields.items() if value not in (None, "")}

    def _response_summary(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            data = payload.get("data")
            summary = {"keys": list(payload.keys())}
            if isinstance(data, dict):
                summary["data_keys"] = list(data.keys())
                for key in ("id", "email", "status"):
                    if key in data:
                        summary[key] = data.get(key)
            elif isinstance(data, list):
                summary["data_len"] = len(data)
            return summary
        return {"type": type(payload).__name__}

    def _log_debug(self, label: str, payload: Any) -> None:
        logger.debug("%s -> %s", label, self._response_summary(payload))

    def _extract_data(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict):
                return data
            return payload
        return {}

    def _extract_id(self, payload: Any) -> Optional[Any]:
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict) and data.get("id") is not None:
                return data.get("id")
            if payload.get("id") is not None:
                return payload.get("id")
        return None

    def _validate_fields(self, fields: Optional[Dict[str, Any]]) -> None:
        if not fields:
            return
        invalid = sorted(set(fields.keys()) - ALLOWED_FIELDS)
        if invalid:
            raise MailerLiteError(
                "Invalid subscriber fields",
                status=400,
                payload={"invalid_fields": invalid},
            )

    def _resolve_group_id(self, group_name: str) -> int:
        if group_name in self._group_cache:
            return self._group_cache[group_name]

        response = self.groups_client.list(
            params={"limit": 1, "page": 1, "filter": {"name": group_name}}
        )
        self._log_debug(f"groups.list filter name={group_name}", response)
        data = response.get("data") if isinstance(response, dict) else None
        if not data:
            raise ValueError(f"MailerLite group not found: {group_name}")
        item = data[0] if isinstance(data, list) else data
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"MailerLite group missing id: {group_name}")
        group_id = int(item.get("id"))
        self._group_cache[group_name] = group_id
        return group_id

    def _get_or_create_subscriber(self, email: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        normalized = normalize_email(email)
        if not normalized:
            return None

        cached = self.registry.get(normalized)
        if cached and cached.get("mailerlite_id"):
            try:
                response = self.get(normalized)
                self._log_debug(f"subscribers.get email={normalized}", response)
                data = self._extract_data(response)
                if data.get("id"):
                    return data
            except Exception:
                pass
            return {"id": str(cached.get("mailerlite_id")), "email": normalized}

        try:
            response = self.get(normalized)
            self._log_debug(f"subscribers.get email={normalized}", response)
            data = self._extract_data(response)
            if data.get("id"):
                return data
        except Exception:
            pass

        try:
            response = self.create(normalized, {"fields": fields})
            self._log_debug(f"subscribers.create email={normalized}", response)
            data = self._extract_data(response)
            if not data.get("id"):
                try:
                    refreshed = self.get(normalized)
                    self._log_debug(f"subscribers.get email={normalized} (post-create)", refreshed)
                    data = self._extract_data(refreshed)
                except Exception:
                    pass
            return data
        except Exception as e:
            logger.warning("Unable to create subscriber %s: %s", normalized, e)
            return None

    def _store_registry(self, email: str, subscriber_id: Optional[str]):
        if not subscriber_id:
            return
        try:
            self.registry.upsert(email, str(subscriber_id))
        except Exception as e:
            logger.warning("Unable to store registry for %s: %s", email, e)

    def _activate_if_needed(self, email: str, data: Dict[str, Any]):
        status = str(data.get("status") or "").lower()
        if status and status != "active":
            try:
                self.update(email, {"status": "active", "resubscribe": True})
            except Exception as e:
                logger.warning("Unable to activate subscriber %s: %s", email, e)

    def sync_newsletter_consent(
        self,
        email: str,
        fields: Dict[str, Any],
        opted_in_at: Optional[str] = None,
    ) -> Optional[str]:
        group_id = self._resolve_group_id(MAILERLITE_GROUP_NEWSLETTER)

        compact_fields = self._compact_fields(fields)
        try:
            self._validate_fields(compact_fields)
        except MailerLiteError as e:
            logger.warning("Invalid fields for %s: %s", email, e.payload or e)
            return None
        subscriber = self._get_or_create_subscriber(email, compact_fields)
        if not subscriber:
            return None

        subscriber_id = subscriber.get("id")
        self._store_registry(email, subscriber_id)
        self._activate_if_needed(email, subscriber)

        if compact_fields:
            try:
                response = self.update(email, {"fields": compact_fields})
                self._log_debug(f"subscribers.update fields email={email}", response)
            except Exception as e:
                logger.warning("Unable to update fields for %s: %s", email, e)

        if opted_in_at:
            try:
                response = self.update(email, {"opted_in_at": opted_in_at})
                self._log_debug(f"subscribers.update opted_in_at email={email}", response)
            except Exception as e:
                logger.warning("Unable to set opted_in_at for %s: %s", email, e)

        try:
            response = self.groups_client.assign_subscriber(subscriber_id, group_id)
            self._log_debug(
                f"groups.assign subscriber_id={subscriber_id} group_id={group_id}", response
            )
        except Exception as e:
            logger.warning("Unable to assign %s to newsletter group: %s", email, e)
        return subscriber_id

    def sync_membership(
        self,
        email: str,
        fields: Dict[str, Any],
    ) -> Optional[str]:
        group_id = self._resolve_group_id(MAILERLITE_GROUP_MEMBERSHIPS)

        compact_fields = self._compact_fields(fields)
        try:
            self._validate_fields(compact_fields)
        except MailerLiteError as e:
            logger.warning("Invalid fields for %s: %s", email, e.payload or e)
            return None
        subscriber = self._get_or_create_subscriber(email, compact_fields)
        if not subscriber:
            return None

        subscriber_id = subscriber.get("id")
        self._store_registry(email, subscriber_id)
        self._activate_if_needed(email, subscriber)

        if compact_fields:
            try:
                response = self.update(email, {"fields": compact_fields})
                self._log_debug(f"subscribers.update fields email={email}", response)
            except Exception as e:
                logger.warning("Unable to update fields for %s: %s", email, e)

        try:
            response = self.groups_client.assign_subscriber(subscriber_id, group_id)
            self._log_debug(
                f"groups.assign subscriber_id={subscriber_id} group_id={group_id}", response
            )
        except Exception as e:
            logger.warning("Unable to assign %s to memberships group: %s", email, e)
        return subscriber_id
