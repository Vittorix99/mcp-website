from enum import Enum

class PurchaseTypes(str, Enum):
    EVENT = "event"                       # acquisto semplice per un evento
    MEMBERSHIP = "membership"             # acquisto della sola membership
    EVENT_AND_MEMBERSHIP = "event_and_membership"   # primo evento: membership + evento insieme
    EVENT_OR_EVENT_AND_MEMBERSHIP = "event_or_event_and_membership"  # EP13: alcuni già membri, altri no
