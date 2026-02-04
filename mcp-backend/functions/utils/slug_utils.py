import re
import unicodedata


def slugify(value: str, max_length: int = 80) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text or "item"


def build_slug(*parts, suffix: str | None = None, max_length: int = 80) -> str:
    base = " ".join([str(p) for p in parts if p])
    base_slug = slugify(base, max_length=max_length)
    if suffix:
        suffix_slug = slugify(str(suffix), max_length=20)
        if suffix_slug:
            return f"{base_slug}-{suffix_slug}"
    return base_slug
