import { safeFetch } from "@/lib/fetch"
import { endpoints } from "@/config/endpoints"

export async function getAdminStats() {
  return safeFetch(endpoints.admin.getGeneralStats, "GET")
}

export async function getDashboardSnapshot() {
  return safeFetch(endpoints.admin.getDashboardSnapshot, "GET")
}

export async function getAnalyticsEventsIndex() {
  return safeFetch(endpoints.admin.getAnalyticsEventsIndex, "GET")
}

export async function getAnalyticsEventSnapshot(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getAnalyticsEventSnapshot}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getAnalyticsGlobalSnapshot() {
  return safeFetch(endpoints.admin.getAnalyticsGlobalSnapshot, "GET")
}

export async function rebuildAnalytics(scope = "all", eventId = null) {
  return safeFetch(endpoints.admin.rebuildAnalytics, "POST", { scope, event_id: eventId })
}

// ---- Live analytics endpoints -------------------------------------------

export async function getEntranceFlow(eventId, options = {}) {
  if (!eventId) return { error: "eventId mancante" }
  const params = new URLSearchParams({ event_id: String(eventId) })
  if (options.startTime) params.set("start_time", String(options.startTime))
  if (options.spanHours) params.set("span_hours", String(options.spanHours))
  if (options.bucketMinutes) params.set("bucket_minutes", String(options.bucketMinutes))
  return safeFetch(`${endpoints.admin.getEntranceFlow}?${params.toString()}`, "GET")
}

export async function getSalesOverTime(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getSalesOverTime}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getAudienceRetention(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getAudienceRetention}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getRevenueBreakdown(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getRevenueBreakdown}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getEventFunnel(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getEventFunnel}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getGenderDistribution(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getGenderDistribution}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getAgeDistribution(eventId) {
  if (!eventId) return { error: "eventId mancante" }
  return safeFetch(`${endpoints.admin.getAgeDistribution}?event_id=${encodeURIComponent(eventId)}`, "GET")
}

export async function getMembershipTrend(year) {
  const url = year
    ? `${endpoints.admin.getMembershipTrend}?year=${encodeURIComponent(year)}`
    : endpoints.admin.getMembershipTrend
  return safeFetch(url, "GET")
}

export async function getDashboardKpis() {
  return safeFetch(endpoints.admin.getDashboardKpis, "GET")
}
