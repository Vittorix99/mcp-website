import { safePublicFetch } from "@/lib/fetch"
import { endpoints } from "@/config/endpoints"

export async function getNextEvent() {
  const res = await safePublicFetch(endpoints.getNextEvent, "GET")
  if (!res.success) {
    return { success: false, error: res.error, events: [] }
  }

  const events = Array.isArray(res.data) ? res.data : []
  return { success: true, events }
}

export async function getEventById(eventId) {
  const url = `${endpoints.getEventById}?id=${encodeURIComponent(eventId)}`
  const res = await safePublicFetch(url, "GET")
  if (!res.success) {
    return { success: false, error: res.error }
  }

  return { success: true, event: res.data }
}

export async function getAllEvents(options = {}) {
  const params = new URLSearchParams()
  if (options.view) params.set("view", options.view)
  const url = params.toString() ? `${endpoints.getAllEvents}?${params.toString()}` : endpoints.getAllEvents

  const res = await safePublicFetch(url, "GET")
  if (!res.success) {
    return { success: false, error: res.error }
  }

  const events = Array.isArray(res.data) ? res.data : []
  return { success: true, events }
}
