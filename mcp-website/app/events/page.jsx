import EventsClient from "./EventsClient"
import { buildEventsItemListJsonLd } from "@/lib/seo/jsonld"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()
export const metadata = {
  title: "Events | Music Connecting People",
  description: "Discover upcoming and past events from Music Connecting People.",
  alternates: baseUrl ? { canonical: `${baseUrl}/events` } : undefined,
}

export default function AllEvents() {
  const jsonLd = buildEventsItemListJsonLd({
    items: [],
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
      <EventsClient />
    </>
  )
}
