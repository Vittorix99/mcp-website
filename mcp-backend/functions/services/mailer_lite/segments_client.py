from typing import Any, Dict, Optional

from .client import MailerLiteClient, filter_kwargs


class SegmentsClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "page"})
        return self.client.call(self.client.sdk.segments.list, **kwargs)

    def get(self, segment_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "filter"})
        return self.client.call(self.client.sdk.segments.get, segment_id, **kwargs)

    def update(self, segment_id: str, name: str) -> Any:
        return self.client.call(self.client.sdk.segments.update, segment_id, name)

    def delete(self, segment_id: str) -> Any:
        return self.client.call(self.client.sdk.segments.delete, segment_id)

    def subscribers(self, segment_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "filter"})
        return self.client.call(self.client.sdk.segments.get_subscribers, segment_id, **kwargs)
