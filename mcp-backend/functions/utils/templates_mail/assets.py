import base64
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
_DEFAULT_WEBSITE_URL = "https://musiconnectingpeople.com"


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


def _force_white_logo(url: str) -> str:
    normalized = _normalize_firebase_logo_url(url)
    if "logo_black.png" in normalized:
        return normalized.replace("logo_black.png", "logo_white.png")
    return normalized


def resolve_logo_url() -> str:
    email_logo = (os.getenv("EMAIL_LOGO_URL") or "").strip()
    if email_logo and email_logo != "#":
        return _force_white_logo(email_logo)

    mailersend_logo = (os.getenv("MAILERSEND_LOGO_URL") or "").strip()
    if mailersend_logo and mailersend_logo != "#":
        return _force_white_logo(mailersend_logo)

    legacy_logo = (os.getenv("LOGO_URL") or "").strip()
    if legacy_logo and legacy_logo != "#":
        return _force_white_logo(legacy_logo)

    bucket = (os.getenv("STORAGE_BUCKET") or "").strip()
    if bucket:
        return f"https://storage.googleapis.com/{bucket}/logos/logo_white.png"

    return "#"


def resolve_instagram_url() -> str:
    return (os.getenv("INSTAGRAM_URL") or DEFAULT_INSTAGRAM_URL).strip()


def resolve_logo_black_url() -> str:
    return _load_asset_as_data_uri("logo_white.png")


def _resolve_public_asset_url(filename: str, env_key: str) -> str:
    explicit_url = (os.getenv(env_key) or "").strip()
    if explicit_url and explicit_url != "#":
        return explicit_url

    website_base = (
        os.getenv("WEBSITE_URL")
        or os.getenv("PUBLIC_WEBSITE_URL")
        or os.getenv("MCP_WEBSITE_URL")
        or _DEFAULT_WEBSITE_URL
    )
    website_base = (website_base or "").strip().rstrip("/")
    if website_base and website_base != "#":
        return f"{website_base}/{filename.lstrip('/')}"

    return ""


def resolve_apple_wallet_url() -> str:
    return _resolve_public_asset_url("apple_wallet.png", "APPLE_WALLET_BUTTON_URL") or _load_asset_as_data_uri(
        "apple_wallet.png"
    )


def resolve_google_wallet_url() -> str:
    return _resolve_public_asset_url("google_wallet.png", "GOOGLE_WALLET_BUTTON_URL") or _load_asset_as_data_uri(
        "google_wallet.png"
    )
