import EventPhotosClient from "./EventPhotosClient"
import { buildEventPhotosCollectionJsonLd } from "@/lib/seo/jsonld"

export const metadata = {
  title: "Event Photos | Music Connecting People",
  description: "Browse photo galleries from Music Connecting People events.",
}

export const revalidate = 300

export default function EventPhotosPage() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.SITE_URL || ""
  const jsonLd = buildEventPhotosCollectionJsonLd({
    items: [],
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
      <EventPhotosClient />
    </>
  )
}
