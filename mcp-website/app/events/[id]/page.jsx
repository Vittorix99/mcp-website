import { EventContent } from "./content"
import { endpoints } from "@/config/endpoints"

export const dynamic = "force-dynamic"

const EVENT_REVALIDATE_SECONDS = 60
const SETTINGS_REVALIDATE_SECONDS = 120
const SETTING_KEYS = ["payment_blocked", "company_iban", "company_intestatario"]

async function fetchEvent(eventId) {
  try {
    const url = `${endpoints.getEventById}?id=${encodeURIComponent(eventId)}`
    const res = await fetch(url, {
      cache: "no-store",
      next: { revalidate: EVENT_REVALIDATE_SECONDS },
    })
    if (!res.ok) {
      const errorPayload = await res.json().catch(() => ({}))
      return { success: false, error: errorPayload?.error || "Evento non trovato" }
    }

    const raw = await res.json()
    if (!raw) return { success: false, error: "Evento non disponibile" }

    return { success: true, event: raw }
  } catch (error) {
    return { success: false, error: error.message || "Errore durante il caricamento dell'evento" }
  }
}

async function fetchSettingValue(key) {
  try {
    const url = `${endpoints.admin.getSetting}?key=${encodeURIComponent(key)}`
    const res = await fetch(url, {
      cache: "force-cache",
      next: { revalidate: SETTINGS_REVALIDATE_SECONDS },
    })
    if (!res.ok) return null
    const data = await res.json().catch(() => null)
    return data?.value ?? null
  } catch {
    return null
  }
}

async function fetchSettings() {
  const [paymentBlocked, iban, intestatario] = await Promise.all(
    SETTING_KEYS.map((key) => fetchSettingValue(key))
  )
  return {
    payment_blocked: Boolean(paymentBlocked),
    company_iban: iban ? String(iban) : "",
    company_intestatario: intestatario ? String(intestatario) : "",
  }
}

export default async function EventPage({ params }) {
  const { id } = await params

  const [eventResult, settings] = await Promise.all([fetchEvent(id), fetchSettings()])

  return <EventContent id={id} event={eventResult.event} settings={settings} error={eventResult.error} />
}
