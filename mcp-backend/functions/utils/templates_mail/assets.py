import base64
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


def _load_asset_as_data_uri(filename: str) -> str:
    path = _ASSETS_DIR / filename
    if path.exists():
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{data}"
    return ""


DEFAULT_INSTAGRAM_URL = "https://www.instagram.com/musiconnectingpeople_/"


def _normalize_firebase_logo_url(url: str) -> str:
    """
    Convert Firebase token-based download URLs to stable GCS public URLs when possible.
    Example:
      https://firebasestorage.googleapis.com/v0/b/<bucket>/o/logos%2Flogo_white.png?... ->
      https://storage.googleapis.com/<bucket>/logos/logo_white.png
    """
    if not url:
        return url

    parsed = urlparse(url)
    if parsed.netloc != "firebasestorage.googleapis.com":
        return url

    parts = parsed.path.strip("/").split("/")
    # Expected path shape: /v0/b/<bucket>/o/<encoded-object>
    if len(parts) < 5 or parts[0] != "v0" or parts[1] != "b" or parts[3] != "o":
        return url

    bucket = parts[2]
    object_path = unquote("/".join(parts[4:]))
    if not bucket or not object_path:
        return url

    return f"https://storage.googleapis.com/{bucket}/{object_path}"


def resolve_logo_url() -> str:
    email_logo = (os.getenv("EMAIL_LOGO_URL") or "").strip()
    if email_logo and email_logo != "#":
        return _normalize_firebase_logo_url(email_logo)

    mailersend_logo = (os.getenv("MAILERSEND_LOGO_URL") or "").strip()
    if mailersend_logo and mailersend_logo != "#":
        return _normalize_firebase_logo_url(mailersend_logo)

    legacy_logo = (os.getenv("LOGO_URL") or "").strip()
    if legacy_logo and legacy_logo != "#":
        return _normalize_firebase_logo_url(legacy_logo)

    bucket = (os.getenv("STORAGE_BUCKET") or "").strip()
    if bucket:
        return f"https://storage.googleapis.com/{bucket}/logos/logo_white.png"

    return "#"


def resolve_instagram_url() -> str:
    return (os.getenv("INSTAGRAM_URL") or DEFAULT_INSTAGRAM_URL).strip()


def resolve_logo_black_url() -> str:
    return _load_asset_as_data_uri("logo_black.png")


def resolve_apple_wallet_url() -> str:
    return _load_asset_as_data_uri("apple_wallet.png")


def resolve_google_wallet_url() -> str:
    return _load_asset_as_data_uri("google_wallet.png")
