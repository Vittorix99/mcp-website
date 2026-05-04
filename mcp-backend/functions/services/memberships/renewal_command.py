from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RenewMembershipCommand:
    """Comando interno per rinnovare una membership senza dipendere da DTO API."""

    membership_id: str
    start_date: str
    end_date: str
    purchase_id: Optional[str] = None
    fee: Optional[float] = None
    membership_type: Optional[str] = None
    send_card: bool = False
    invalidate_wallet: bool = True
    create_wallet: bool = True
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    birthdate: Optional[str] = None
