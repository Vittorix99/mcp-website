
import HomeClient from "./HomeClient"
import { buildOrganizationJsonLd } from "@/lib/seo/jsonld"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"
import { getNextEvent } from "@/services/events"
import { getPublishedEpisodes } from "@/services/radio"

const baseUrl = getBaseUrlFromEnv()
export const metadata = {
  title: "Music Connecting People",
  description: "Experience the rhythm. Connect with the community.",
  alternates: baseUrl ? { canonical: `${baseUrl}/` } : undefined,
}

export default async function LandingPage() {
  const orgJsonLd = buildOrganizationJsonLd({
    siteName: "Music Connecting People",
    siteUrl: baseUrl,
  })

  let nextEvent = null
  try {
    const res = await getNextEvent()
    if (res?.success) nextEvent = res.events?.[0] ?? null
  } catch {}

  let radioEpisodes = []
  try {
    const res = await getPublishedEpisodes({ revalidate: 300 })
    if (res?.success) radioEpisodes = res.episodes
  } catch {}

  return (
    <>
      {orgJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
        />
      )}
      <HomeClient nextEvent={nextEvent} radioEpisodes={radioEpisodes} />
    </>
  )
}
