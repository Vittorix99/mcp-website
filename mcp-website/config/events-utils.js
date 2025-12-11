import dynamic from "next/dynamic"

const DEFAULT_MEMBERSHIP_FEE = Number(process.env.NEXT_PUBLIC_MEMBERSHIP_FEE ?? 10)

export const PURCHASE_MODES = Object.freeze({
  PUBLIC: "PUBLIC",
  ONLY_ALREADY_REGISTERED_MEMBERS: "ONLY_ALREADY_REGISTERED_MEMBERS",
  ONLY_MEMBERS: "ONLY_MEMBERS",
  ON_REQUEST: "ON_REQUEST",
})

const LEGACY_MAP = {
  standard: PURCHASE_MODES.PUBLIC,
  free: PURCHASE_MODES.PUBLIC,
  custom_ep12: PURCHASE_MODES.PUBLIC,
  external: PURCHASE_MODES.PUBLIC,
  external_link: PURCHASE_MODES.PUBLIC,
  community: PURCHASE_MODES.ONLY_MEMBERS,
  onlymembers: PURCHASE_MODES.ONLY_MEMBERS,
  only_members: PURCHASE_MODES.ONLY_MEMBERS,
  custom_ep13: PURCHASE_MODES.ONLY_MEMBERS,
  "only already registered members": PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS,
  onlyalreadyregisteredmembers: PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS,
  only_already_registered_members: PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS,
  private: PURCHASE_MODES.ON_REQUEST,
  onrequest: PURCHASE_MODES.ON_REQUEST,
  on_request: PURCHASE_MODES.ON_REQUEST,
}

export function normalizePurchaseMode(value) {
  if (!value) return PURCHASE_MODES.PUBLIC

  const raw = String(value).trim()
  const lower = raw.toLowerCase()
  if (LEGACY_MAP[lower]) return LEGACY_MAP[lower]

  const normalized = raw.replace(/[\s-]+/g, "_").toUpperCase()
  if (PURCHASE_MODES[normalized]) return PURCHASE_MODES[normalized]

  return PURCHASE_MODES.PUBLIC
}

export function resolvePurchaseMode(event) {
  if (!event) return PURCHASE_MODES.PUBLIC
  return normalizePurchaseMode(event.purchase_mode || event.purchaseMode || event.type)
}

export function ensureMembershipFee(value) {
  const fee = Number(value)
  if (!Number.isFinite(fee) || fee <= 0) return DEFAULT_MEMBERSHIP_FEE
  return fee
}

export const EVENT_CONTENT_COMPONENT = dynamic(() =>
  import("@/components/pages/events/event-types/EventPurchaseContent"),
)
