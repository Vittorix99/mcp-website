class DummyRequest:
    def __init__(self, method="GET", json=None, args=None, headers=None):
        self.method = method
        self._json = json
        self.args = args or {}
        self.headers = headers or {"Authorization": "Bearer test-token"}

    def get_json(self):
        return self._json


def unwrap_response(result):
    if isinstance(result, tuple):
        return result
    if hasattr(result, "get_json") and hasattr(result, "status_code"):
        payload = result.get_json(silent=True) or {}
        return payload, result.status_code
    return result, None
