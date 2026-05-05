import RadioClient from "./RadioClient"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"
import { buildRadioEpisodesItemListJsonLd } from "@/lib/seo/jsonld"
import { getPublishedEpisodes, getRadioSeasons } from "@/services/radio"

const baseUrl = getBaseUrlFromEnv()

export const metadata = {
  title: "MCP Radio — Music Connecting People",
  description: "Listen to our radio episodes on SoundCloud. Electronic music mixes from MCP events and beyond.",
  alternates: baseUrl ? { canonical: `${baseUrl}/radio` } : undefined,
  openGraph: {
    title: "MCP Radio — Music Connecting People",
    description: "Listen to our radio episodes on SoundCloud. Electronic music mixes from MCP events and beyond.",
    url: baseUrl ? `${baseUrl}/radio` : undefined,
    type: "website",
  },
}

export default async function RadioPage() {
  const [episodesRes, seasonsRes] = await Promise.all([
    getPublishedEpisodes({ revalidate: 300 }),
    getRadioSeasons({ revalidate: 600 }),
  ])
  const initialEpisodes = episodesRes?.episodes || []
  const initialSeasons = seasonsRes?.seasons || []
  const jsonLd = buildRadioEpisodesItemListJsonLd({
    items: initialEpisodes,
    baseUrl,
    listUrl: baseUrl ? `${baseUrl}/radio` : "",
  })

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <RadioClient initialEpisodes={initialEpisodes} initialSeasons={initialSeasons} />
    </>
  )
}
