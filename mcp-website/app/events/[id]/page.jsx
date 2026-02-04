import { EventContent } from "./content"
import { endpoints } from "@/config/endpoints"
import { getBaseUrlFromHeaders } from "@/lib/seo/base-url"
import { buildEventJsonLd } from "@/lib/seo/jsonld"

export const dynamic = "force-dynamic"

const EVENT_REVALIDATE_SECONDS = 60
const SETTINGS_REVALIDATE_SECONDS = 120
const SETTING_KEYS = ["payment_blocked", "company_iban", "company_intestatario"]


async function fetchEvent(eventId) {
  try {
    const key = encodeURIComponent(eventId)
    const url = `${endpoints.getEventById}?slug=${key}&id=${key}`
    const res = await fetch(url, {
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

export async function generateMetadata({ params }) {
  const { id } = await params
  const result = await fetchEvent(id)
  const title = result?.event?.title ? `${result.event.title} | MCP Event` : "Event | Music Connecting People"
  const description = result?.event?.locationHint
    ? `${result.event.locationHint} · ${result.event.date || ""}`.trim()
    : "Discover events by Music Connecting People."
  const baseUrl = await getBaseUrlFromHeaders()
  const canonical = baseUrl ? `${baseUrl}/events/${id}` : undefined

  return {
    title,
    description,
    alternates: canonical ? { canonical } : undefined,
    openGraph: {
      title,
      description,
      url: canonical,
      type: "article",
    },
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
  const baseUrl = await getBaseUrlFromHeaders()
  const jsonLd = eventResult?.event
    ? buildEventJsonLd({
        event: eventResult.event,
        url: baseUrl ? `${baseUrl}/events/${id}` : undefined,
        siteUrl: baseUrl,
      })
    : null

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <EventContent id={id} event={eventResult.event} settings={settings} error={eventResult.error} />
    </>
  )
}
