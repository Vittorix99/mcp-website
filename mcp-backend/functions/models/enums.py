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



class PurchaseTypes(str, Enum):
    EVENT = "event"
    MEMBERSHIP = "membership" 
