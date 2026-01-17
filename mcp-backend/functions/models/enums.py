from enum import Enum


class EventPurchaseAccessType(str, Enum):
    """
    Defines how users can acquire access to an event. Replaces the legacy
    event ``type`` classification so services can reason directly on the
    purchase rules.
    """

    PUBLIC = "PUBLIC"
    ONLY_ALREADY_REGISTERED_MEMBERS = "ONLY_ALREADY_REGISTERED_MEMBERS"
    ONLY_MEMBERS = "ONLY_MEMBERS"
    ON_REQUEST = "ON_REQUEST"



class EventStatus(str, Enum):
    COMING_SOON = "coming_soon"
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    ENDED = "ended"


class PaymentMethod(str, Enum):
    WEBSITE = "website"
    PRIVATE_PAYPAL = "private_paypal"
    IBAN = "iban"
    CASH = "cash"
    OMAGGIO = "omaggio"


class PurchaseTypes(str, Enum):
    EVENT = "event"
    MEMBERSHIP = "membership" 
