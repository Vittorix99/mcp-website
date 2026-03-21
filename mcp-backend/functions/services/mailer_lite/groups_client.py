from typing import Any, Dict, Optional

from .client import MailerLiteClient, filter_kwargs


class GroupsClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()

    def _to_int(self, value: Any, label: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be int-compatible, got {value!r}")

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "page", "filter", "sort"})
        return self.client.call(self.client.sdk.groups.list, **kwargs)

    def create(self, name: str) -> Any:
        return self.client.call(self.client.sdk.groups.create, name)

    def update(self, group_id: str, name: str) -> Any:
        group_id = self._to_int(group_id, "group_id")
        return self.client.call(self.client.sdk.groups.update, group_id, name)

    def delete(self, group_id: str) -> Any:
        group_id = self._to_int(group_id, "group_id")
        response = self.client.call(self.client.sdk.groups.delete, group_id)
        if isinstance(response, (bool, int)):
            return {"status": response}
        return response

    def subscribers(self, group_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"page", "limit", "filter"})
        group_id = self._to_int(group_id, "group_id")
        return self.client.call(self.client.sdk.groups.get_group_subscribers, group_id, **kwargs)

    def assign_subscriber(self, subscriber_id: str, group_id: str) -> Any:
        subscriber_id = self._to_int(subscriber_id, "subscriber_id")
        group_id = self._to_int(group_id, "group_id")
        response = self.client.call(
            self.client.sdk.subscribers.assign_subscriber_to_group, subscriber_id, group_id
        )
        if isinstance(response, (bool, int)):
            return {"status": response}
        return response

    def unassign_subscriber(self, subscriber_id: str, group_id: str) -> Any:
        subscriber_id = self._to_int(subscriber_id, "subscriber_id")
        group_id = self._to_int(group_id, "group_id")
        response = self.client.call(
            self.client.sdk.subscribers.unassign_subscriber_from_group, subscriber_id, group_id
        )
        if isinstance(response, (bool, int)):
            return {"status": response}
        return response
