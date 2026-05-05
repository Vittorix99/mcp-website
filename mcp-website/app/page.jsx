
import HomeClient from "./HomeClient"
import { buildOrganizationJsonLd } from "@/lib/seo/jsonld"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"
import { getNextEvent } from "@/services/events"

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
    if (res?.success) nextEvent = res.events?.[0] ?? res.event ?? res.data ?? null
  } catch {}

  let radioEpisodes = []
  try {
    const SERVER_BASE =
      process.env.NEXT_PUBLIC_ENV === "production"
        ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
        : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1"
    const res = await fetch(`${SERVER_BASE}/get_published_radio_episodes`, { next: { revalidate: 300 } })
    if (res.ok) radioEpisodes = await res.json()
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
