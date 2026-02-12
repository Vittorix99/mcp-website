from types import SimpleNamespace

from services.mailer_lite.campaigns_client import CampaignsClient


class _DummyClient:
    def __init__(self, sdk):
        self.sdk = sdk
        self.calls = []

    def call(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return {"ok": True}


def test_campaigns_list_filters_params():
    """Only allowed list params are forwarded to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(list=lambda **kwargs: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.list(params={"limit": 10, "page": 2, "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.list
    assert args == ()
    assert kwargs == {"limit": 10, "page": 2, "filter": {"x": 1}}


def test_campaigns_get_calls_sdk():
    """Get forwards id to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(get=lambda campaign_id: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.get("camp-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.get
    assert args == ("camp-1",)
    assert kwargs == {}


def test_campaigns_create_calls_sdk():
    """Create forwards payload to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(create=lambda payload: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.create({"name": "Test"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.create
    assert args == ({"name": "Test"},)
    assert kwargs == {}


def test_campaigns_update_calls_sdk():
    """Update forwards id and payload to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(update=lambda campaign_id, payload: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.update("camp-1", {"name": "Updated"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.update
    assert args == ("camp-1", {"name": "Updated"})
    assert kwargs == {}


def test_campaigns_schedule_calls_sdk():
    """Schedule forwards id and payload to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(schedule=lambda campaign_id, payload: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.schedule("camp-1", {"delivery": "scheduled"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.schedule
    assert args == ("camp-1", {"delivery": "scheduled"})
    assert kwargs == {}


def test_campaigns_cancel_ready_calls_sdk():
    """Cancel forwards id to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(cancel=lambda campaign_id: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.cancel_ready("camp-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.cancel
    assert args == ("camp-1",)
    assert kwargs == {}


def test_campaigns_delete_calls_sdk():
    """Delete forwards id to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(delete=lambda campaign_id: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.delete("camp-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.delete
    assert args == ("camp-1",)
    assert kwargs == {}


def test_campaigns_activity_calls_sdk():
    """Activity forwards id to the SDK."""
    sdk = SimpleNamespace(campaigns=SimpleNamespace(activity=lambda campaign_id: None))
    client = _DummyClient(sdk)
    campaigns = CampaignsClient(client=client)

    campaigns.activity("camp-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.campaigns.activity
    assert args == ("camp-1",)
    assert kwargs == {}
