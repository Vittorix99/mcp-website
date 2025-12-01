from enum import Enum

class EventTypes(str, Enum):
    STANDARD = "standard"
    COMMUNITY = "community"
    FREE = "free"
    PRIVATE = "private"
    CUSTOM_EP12 = "custom_ep12"
    CUSTOM_EP13 = "custom_ep13"
    EXTERNAL = "external_link"