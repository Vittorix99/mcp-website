from dto.templates import MembershipEmailPayload
from services.templates import render_template

from .assets import resolve_apple_wallet_url, resolve_google_wallet_url, resolve_logo_url


def _extract_year(expiry_date: str) -> str:
    if isinstance(expiry_date, str) and "-" in expiry_date:
        return expiry_date.split("-")[-1]
    return "N/A"


def get_membership_email_template(membership_data, pdf_url=None):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    expiry_date = membership_data.get("end_date") or "N/A"
    payload = MembershipEmailPayload(
        logo_url=resolve_logo_url(),
        full_name=full_name,
        membership_id=membership_data.get("membership_id", ""),
        expiry_date=expiry_date,
        membership_year=_extract_year(expiry_date),
        wallet_url=membership_data.get("wallet_url") or None,
        pdf_url=pdf_url,
        apple_wallet_img=resolve_apple_wallet_url() or None,
        google_wallet_img=resolve_google_wallet_url() or None,
    )
    return render_template("emails/membership.html", payload)


def get_membership_email_text(membership_data):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date") or "N/A"
    year = _extract_year(expiry_date)
    wallet_url = membership_data.get("wallet_url") or ""

    wallet_section = ""
    if wallet_url:
        wallet_section = f"\nAggiungi la tua tessera al wallet (apri dal tuo smartphone):\n{wallet_url}\n"

    return f"""Ciao {full_name},

grazie per esserti iscritto all'Associazione Music Connecting People!

Membership ID: {membership_id}
Validità: fino al {expiry_date}
{wallet_section}
Membro dell'Associazione Music Connecting People ETS – Anno {year}
"""
