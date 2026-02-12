from types import SimpleNamespace

from services.mailer_lite.automations_client import AutomationsClient


class _DummyClient:
    def __init__(self, sdk):
        self.sdk = sdk
        self.calls = []

    def call(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return {"ok": True}


def test_automations_list_filters_params():
    """Only allowed list params are forwarded to the SDK."""
    sdk = SimpleNamespace(automations=SimpleNamespace(list=lambda **kwargs: None))
    client = _DummyClient(sdk)
    automations = AutomationsClient(client=client)

    automations.list(params={"limit": 10, "page": 2, "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.automations.list
    assert args == ()
    assert kwargs == {"limit": 10, "page": 2, "filter": {"x": 1}}


def test_automations_get_calls_sdk():
    """Get forwards id to the SDK."""
    sdk = SimpleNamespace(automations=SimpleNamespace(get=lambda automation_id: None))
    client = _DummyClient(sdk)
    automations = AutomationsClient(client=client)

    automations.get("auto-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.automations.get
    assert args == ("auto-1",)
    assert kwargs == {}


def test_automations_activity_filters_params():
    """Activity forwards id and allowed params."""
    sdk = SimpleNamespace(automations=SimpleNamespace(activity=lambda automation_id, **kwargs: None))
    client = _DummyClient(sdk)
    automations = AutomationsClient(client=client)

    automations.activity("auto-1", params={"page": 2, "limit": 10, "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.automations.activity
    assert args == ("auto-1",)
    assert kwargs == {"page": 2, "limit": 10, "filter": {"x": 1}}
