from typing import Any, Dict, Optional

from .client import MailerLiteClient, filter_kwargs


class AutomationsClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "page", "filter"})
        return self.client.call(self.client.sdk.automations.list, **kwargs)

    def get(self, automation_id: str) -> Any:
        return self.client.call(self.client.sdk.automations.get, automation_id)

    def activity(self, automation_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"page", "limit", "filter"})
        return self.client.call(self.client.sdk.automations.activity, automation_id, **kwargs)
