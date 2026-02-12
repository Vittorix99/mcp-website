from types import SimpleNamespace

from services.mailer_lite.fields_client import FieldsClient


class _DummyClient:
    def __init__(self, sdk):
        self.sdk = sdk
        self.calls = []

    def call(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return {"ok": True}


def test_fields_list_filters_params():
    """Only allowed list params are forwarded to the SDK."""
    sdk = SimpleNamespace(fields=SimpleNamespace(list=lambda **kwargs: None))
    client = _DummyClient(sdk)
    fields = FieldsClient(client=client)

    fields.list(params={"limit": 10, "page": 2, "sort": "name", "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.fields.list
    assert args == ()
    assert kwargs == {"limit": 10, "page": 2, "sort": "name", "filter": {"x": 1}}


def test_fields_create_calls_sdk():
    """Create forwards name and type to the SDK."""
    sdk = SimpleNamespace(fields=SimpleNamespace(create=lambda name, field_type: None))
    client = _DummyClient(sdk)
    fields = FieldsClient(client=client)

    fields.create("phone", "text")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.fields.create
    assert args == ("phone", "text")
    assert kwargs == {}


def test_fields_update_calls_sdk():
    """Update forwards id and name to the SDK."""
    sdk = SimpleNamespace(fields=SimpleNamespace(update=lambda field_id, name: None))
    client = _DummyClient(sdk)
    fields = FieldsClient(client=client)

    fields.update("123", "new_name")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.fields.update
    assert args == ("123", "new_name")
    assert kwargs == {}


def test_fields_delete_calls_sdk():
    """Delete forwards id to the SDK."""
    sdk = SimpleNamespace(fields=SimpleNamespace(delete=lambda field_id: None))
    client = _DummyClient(sdk)
    fields = FieldsClient(client=client)

    fields.delete("123")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.fields.delete
    assert args == ("123",)
    assert kwargs == {}
