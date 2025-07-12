// utils/eventTypes.js
import dynamic from "next/dynamic"

export const EVENT_TYPES = Object.freeze({
  STANDARD:    "standard",
  COMMUNITY:   "community",
  FREE:        "free",
  PRIVATE:     "private",
  CUSTOM_EP12: "custom_ep12",
  EXTERNAL: "external_link"
});

export const EVENT_COMPONENTS = {
  [EVENT_TYPES.STANDARD]:    dynamic(() => import("@/components/pages/events/event-types/StandardContent")),
  [EVENT_TYPES.COMMUNITY]:   dynamic(() => import("@/components/pages/events/event-types/CommunityContent")),
  [EVENT_TYPES.PRIVATE]:     dynamic(() => import("@/components/pages/events/event-types/PrivateContent")),
  [EVENT_TYPES.FREE]:        dynamic(() => import("@/components/pages/events/event-types/FreeContent")),
  [EVENT_TYPES.CUSTOM_EP12]: dynamic(() => import("@/components/pages/events/event-types/CustomEp12Content")),
  [EVENT_TYPES.EXTERNAL]: dynamic(() => import("@/components/pages/events/event-types/ExternalLinkContent"))
};