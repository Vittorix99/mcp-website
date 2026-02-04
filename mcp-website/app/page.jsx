import { getNextEvent } from "@/services/events"
import HomeClient from "./HomeClient"
import { getBaseUrlFromHeaders } from "@/lib/seo/base-url"
import { buildOrganizationJsonLd } from "@/lib/seo/jsonld"

export const dynamic = "force-dynamic"
export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
}

async function fetchNextEventOnServer() {
  try {
    const { success, events } = await getNextEvent()
    if (success && Array.isArray(events) && events.length > 0) {
      return { nextEvent: events[0], hasNextEvent: true }
    }
    return { nextEvent: null, hasNextEvent: false }
  } catch {
    return { nextEvent: null, hasNextEvent: false }
  }
}

export default async function LandingPage() {
  const { nextEvent, hasNextEvent } = await fetchNextEventOnServer()
  const baseUrl = await getBaseUrlFromHeaders()
  const orgJsonLd = buildOrganizationJsonLd({
    siteName: "Music Connecting People",
    siteUrl: baseUrl,
  })

  return (
    <>
      {orgJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
        />
      )}
      <HomeClient nextEvent={nextEvent} hasNextEvent={hasNextEvent} />
    </>
  )
}
