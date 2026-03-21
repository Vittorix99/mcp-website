class DummyRequest:
    def __init__(self, method="GET", json=None, args=None, headers=None):
        self.method = method
        self._json = json
        self.args = args or {}
        self.headers = headers or {"Authorization": "Bearer test-token"}

    def get_json(self, *args, **kwargs):
        return self._json


def _extract_response_payload(response):
    data = response.get_json(silent=True)
    if data is not None:
        return data

    if hasattr(response, "get_data"):
        text = response.get_data(as_text=True)
        if text:
            return text

    raw = getattr(response, "data", None)
    if isinstance(raw, (bytes, bytearray)):
        text = raw.decode("utf-8", errors="ignore")
        if text:
            return text

    if isinstance(raw, str) and raw:
        return raw

    return {}


def unwrap_response(result):
    if isinstance(result, tuple):
        payload, status = result
        if hasattr(payload, "get_json") and hasattr(payload, "status_code"):
            data = _extract_response_payload(payload)
            return data, status
        return result
    if hasattr(result, "get_json") and hasattr(result, "status_code"):
        payload = _extract_response_payload(result)
        return payload, result.status_code
    return result, None
