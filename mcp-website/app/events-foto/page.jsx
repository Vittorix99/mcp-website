import EventPhotosClient from "./EventPhotosClient"
import { buildEventPhotosCollectionJsonLd } from "@/lib/seo/jsonld"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"
import { getEventPhotoAlbums } from "@/lib/event-photo-albums"

const baseUrl = getBaseUrlFromEnv()
export const metadata = {
  title: "Event Photos | Music Connecting People",
  description: "Browse photo galleries from Music Connecting People events.",
  alternates: baseUrl ? { canonical: `${baseUrl}/events-foto` } : undefined,
}

export const revalidate = 300

export default async function EventPhotosPage() {
  const { events, error } = await getEventPhotoAlbums()
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
