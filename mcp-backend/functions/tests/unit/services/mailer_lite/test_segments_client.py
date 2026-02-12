from types import SimpleNamespace

from services.mailer_lite.segments_client import SegmentsClient


class _DummyClient:
    def __init__(self, sdk):
        self.sdk = sdk
        self.calls = []

    def call(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return {"ok": True}


def test_segments_list_filters_params():
    """Only allowed list params are forwarded to the SDK."""
    sdk = SimpleNamespace(segments=SimpleNamespace(list=lambda **kwargs: None))
    client = _DummyClient(sdk)
    segments = SegmentsClient(client=client)

    segments.list(params={"limit": 10, "page": 2, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.segments.list
    assert args == ()
    assert kwargs == {"limit": 10, "page": 2}


def test_segments_get_filters_params():
    """Get forwards segment id and allowed params."""
    sdk = SimpleNamespace(segments=SimpleNamespace(get=lambda segment_id, **kwargs: None))
    client = _DummyClient(sdk)
    segments = SegmentsClient(client=client)

    segments.get("seg-1", params={"limit": 5, "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.segments.get
    assert args == ("seg-1",)
    assert kwargs == {"limit": 5, "filter": {"x": 1}}


def test_segments_subscribers_filters_params():
    """Subscribers forwards segment id and allowed params."""
    sdk = SimpleNamespace(segments=SimpleNamespace(get_subscribers=lambda segment_id, **kwargs: None))
    client = _DummyClient(sdk)
    segments = SegmentsClient(client=client)

    segments.subscribers("seg-1", params={"limit": 5, "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.segments.get_subscribers
    assert args == ("seg-1",)
    assert kwargs == {"limit": 5, "filter": {"x": 1}}


def test_segments_update_calls_sdk():
    """Update forwards id and name to the SDK."""
    sdk = SimpleNamespace(segments=SimpleNamespace(update=lambda segment_id, name: None))
    client = _DummyClient(sdk)
    segments = SegmentsClient(client=client)

    segments.update("seg-1", "New Name")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.segments.update
    assert args == ("seg-1", "New Name")
    assert kwargs == {}


def test_segments_delete_calls_sdk():
    """Delete forwards id to the SDK."""
    sdk = SimpleNamespace(segments=SimpleNamespace(delete=lambda segment_id: None))
    client = _DummyClient(sdk)
    segments = SegmentsClient(client=client)

    segments.delete("seg-1")

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.segments.delete
    assert args == ("seg-1",)
    assert kwargs == {}
