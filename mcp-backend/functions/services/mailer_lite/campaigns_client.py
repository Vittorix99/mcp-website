from typing import Any, Dict, Optional

from .client import MailerLiteClient, filter_kwargs


class CampaignsClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "page", "filter"})
        return self.client.call(self.client.sdk.campaigns.list, **kwargs)

    def get(self, campaign_id: str) -> Any:
        return self.client.call(self.client.sdk.campaigns.get, campaign_id)

    def create(self, payload: Dict[str, Any]) -> Any:
        return self.client.call(self.client.sdk.campaigns.create, payload)

    def update(self, campaign_id: str, payload: Dict[str, Any]) -> Any:
        return self.client.call(self.client.sdk.campaigns.update, campaign_id, payload)

    def schedule(self, campaign_id: str, payload: Dict[str, Any]) -> Any:
        return self.client.call(self.client.sdk.campaigns.schedule, campaign_id, payload)

    def cancel_ready(self, campaign_id: str) -> Any:
        return self.client.call(self.client.sdk.campaigns.cancel, campaign_id)

    def delete(self, campaign_id: str) -> Any:
        return self.client.call(self.client.sdk.campaigns.delete, campaign_id)

    def activity(self, campaign_id: str) -> Any:
        return self.client.call(self.client.sdk.campaigns.activity, campaign_id)
