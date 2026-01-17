import dynamic from "next/dynamic"

export const PURCHASE_MODES = Object.freeze({
  PUBLIC: "PUBLIC",
  ONLY_ALREADY_REGISTERED_MEMBERS: "ONLY_ALREADY_REGISTERED_MEMBERS",
  ONLY_MEMBERS: "ONLY_MEMBERS",
  ON_REQUEST: "ON_REQUEST",
})

export const EVENT_STATUSES = Object.freeze({
  COMING_SOON: "coming_soon",
  ACTIVE: "active",
  SOLD_OUT: "sold_out",
  ENDED: "ended",
})

export function normalizePurchaseMode(value) {
  if (!value) return PURCHASE_MODES.PUBLIC

  const raw = String(value).trim()
  const normalized = raw.replace(/[\s-]+/g, "_").toUpperCase()
  if (PURCHASE_MODES[normalized]) return PURCHASE_MODES[normalized]

  return PURCHASE_MODES.PUBLIC
}

export function resolvePurchaseMode(event) {
  if (!event) return PURCHASE_MODES.PUBLIC
  return normalizePurchaseMode(event.purchase_mode || event.purchaseMode)
}

export const EVENT_CONTENT_COMPONENT = dynamic(() =>
  import("@/components/pages/events/event-types/EventPurchaseContent"),
)
