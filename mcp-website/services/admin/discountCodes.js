import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

export async function createDiscountCode(eventId, data) {
  return safeFetch(endpoints.admin.createDiscountCode, "POST", { eventId, ...data })
}

export async function listDiscountCodes(eventId) {
  return safeFetch(`${endpoints.admin.listDiscountCodes}?eventId=${encodeURIComponent(eventId)}`, "GET")
}

export async function getDiscountCode(discountCodeId) {
  return safeFetch(`${endpoints.admin.getDiscountCode}?discountCodeId=${encodeURIComponent(discountCodeId)}`, "GET")
}

export async function updateDiscountCode(discountCodeId, data) {
  return safeFetch(endpoints.admin.updateDiscountCode, "PATCH", { discountCodeId, ...data })
}

export async function disableDiscountCode(discountCodeId) {
  return safeFetch(endpoints.admin.disableDiscountCode, "DELETE", { discountCodeId })
}
