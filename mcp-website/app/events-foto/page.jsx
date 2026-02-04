import { getAllEvents } from "@/services/events"
import EventPhotosClient from "./EventPhotosClient"
import { getBaseUrlFromHeaders } from "@/lib/seo/base-url"
import { buildEventPhotosCollectionJsonLd } from "@/lib/seo/jsonld"

export const dynamic = "force-dynamic"
export const metadata = {
  title: "Event Photos | Music Connecting People",
  description: "Browse photo galleries from Music Connecting People events.",
}

async function fetchEventsOnServer() {
  try {
    const { success, events, error } = await getAllEvents({ view: "gallery" })
    if (!success || !Array.isArray(events)) {
      return { events: [], error: error || "Impossibile recuperare gli eventi." }
    }
    return { events, error: null }
  } catch {
    return { events: [], error: "Errore durante il caricamento degli eventi." }
  }
}

export default async function EventPhotosPage() {
  const { events, error } = await fetchEventsOnServer()
  const baseUrl = await getBaseUrlFromHeaders()
  const jsonLd = buildEventPhotosCollectionJsonLd({
    items: events,
    baseUrl,
    listUrl: baseUrl ? `${baseUrl}/events-foto` : "",
  })

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <EventPhotosClient initialEvents={events} initialError={error} />
    </>
  )
}
