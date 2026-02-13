import time
from typing import Iterable

from googleapiclient.errors import HttpError


READ_SCOPES = {
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
}


def ensure_read_scopes(scopes: Iterable[str]) -> None:
    if not scopes or not any(scope in READ_SCOPES for scope in scopes):
        raise RuntimeError(
            "SCOPES must include gmail.readonly or gmail.modify to verify delivery"
        )


def wait_for_message(service, query: str, retries: int = 8, delay: float = 2.0) -> bool:
    for _ in range(max(retries, 1)):
        try:
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=1)
                .execute()
            )
        except HttpError as exc:  # pragma: no cover - only on misconfigured scopes
            raise RuntimeError(f"Gmail API list failed: {exc}") from exc
        messages = response.get("messages") or []
        if messages:
            return True
        time.sleep(delay)
    return False

