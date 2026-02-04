import { getAllEvents } from "@/services/events"
import EventsClient from "./EventsClient"
import { getBaseUrlFromHeaders } from "@/lib/seo/base-url"
import { buildEventsItemListJsonLd } from "@/lib/seo/jsonld"

export const dynamic = "force-dynamic"
export const metadata = {
  title: "Events | Music Connecting People",
  description: "Discover upcoming and past events from Music Connecting People.",
}

async function fetchEventsOnServer() {
  try {
    const { success, events, error } = await getAllEvents({ view: "card" })
    if (!success || !events) {
      return { events: [], error: error || "Impossibile caricare gli eventi." }
    }
    return { events, error: null }
  } catch {
    return { events: [], error: "Errore imprevisto durante il recupero degli eventi." }
  }
}

export default async function AllEvents() {
  const { events, error } = await fetchEventsOnServer()
  const baseUrl = await getBaseUrlFromHeaders()
  const jsonLd = buildEventsItemListJsonLd({
    items: events,
    baseUrl,
    listUrl: baseUrl ? `${baseUrl}/events` : "",
  })

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <EventsClient initialEvents={events} initialError={error} />
    </>
  )
}
