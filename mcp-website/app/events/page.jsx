import EventsClient from "./EventsClient"
import { buildEventsItemListJsonLd } from "@/lib/seo/jsonld"

export const metadata = {
  title: "Events | Music Connecting People",
  description: "Discover upcoming and past events from Music Connecting People.",
}

export default function AllEvents() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.SITE_URL || ""
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
