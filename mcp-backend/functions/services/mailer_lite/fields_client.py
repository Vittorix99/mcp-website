from typing import Any, Dict, Optional

from .client import MailerLiteClient, filter_kwargs


class FieldsClient:
    def __init__(self, client: Optional[MailerLiteClient] = None):
        self.client = client or MailerLiteClient()

    def list(self, params: Optional[Dict[str, Any]] = None) -> Any:
        kwargs = filter_kwargs(params, {"limit", "page", "sort", "filter"})
        return self.client.call(self.client.sdk.fields.list, **kwargs)

    def create(self, name: str, field_type: str) -> Any:
        return self.client.call(self.client.sdk.fields.create, name, field_type)

    def update(self, field_id: str, name: str) -> Any:
        return self.client.call(self.client.sdk.fields.update, field_id, name)

    def delete(self, field_id: str) -> Any:
        return self.client.call(self.client.sdk.fields.delete, field_id)
