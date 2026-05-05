import EpisodeClient from "./EpisodeClient"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"
import { buildRadioEpisodeJsonLd } from "@/lib/seo/jsonld"
import { getEpisodeSlug } from "@/lib/utils/radio"
import { getPublishedEpisodes, getRadioEpisode } from "@/services/radio"

const baseUrl = getBaseUrlFromEnv()

async function fetchAllEpisodes() {
  const res = await getPublishedEpisodes({ revalidate: 300 })
  return res?.episodes || []
}

async function fetchEpisodeBySlug(slug) {
  const res = await getRadioEpisode(slug, { revalidate: 300 })
  return res?.episode || null
}

export async function generateMetadata({ params }) {
  const { slug } = await params
  const episode = await fetchEpisodeBySlug(slug)
  if (!episode) return { title: "Episode — MCP Radio" }
  const artworkUrl = episode.customArtworkUrl || episode.soundcloudArtworkUrl
  const canonicalSlug = getEpisodeSlug(episode)
  return {
    title: `${episode.title} — MCP Radio`,
    description: episode.description || "Listen to this MCP Radio episode on SoundCloud.",
    openGraph: {
      title: `${episode.title} — MCP Radio`,
      description: episode.description || "Listen to this MCP Radio episode on SoundCloud.",
      url: baseUrl ? `${baseUrl}/radio/${canonicalSlug}` : undefined,
      type: "article",
      images: artworkUrl ? [{ url: artworkUrl }] : undefined,
    },
    alternates: baseUrl ? { canonical: `${baseUrl}/radio/${canonicalSlug}` } : undefined,
  }
}

export default async function EpisodePage({ params }) {
  const { slug } = await params
  const [episode, allEpisodes] = await Promise.all([
    fetchEpisodeBySlug(slug),
    fetchAllEpisodes(),
  ])

  const canonicalSlug = episode ? getEpisodeSlug(episode) : slug

  const jsonLd = episode
    ? buildRadioEpisodeJsonLd({
        episode,
        url: baseUrl ? `${baseUrl}/radio/${canonicalSlug}` : undefined,
        siteUrl: baseUrl,
      })
    : null

  const sameSeasonEps = allEpisodes
    .filter(e => e.seasonId === episode?.seasonId && e.id !== episode?.id)
    .sort((a, b) => (a.episodeNumber || 0) - (b.episodeNumber || 0))

  const epNum = episode?.episodeNumber || 0
  const prevEp = sameSeasonEps.filter(e => (e.episodeNumber || 0) < epNum).at(-1) || null
  const nextEp = sameSeasonEps.find(e => (e.episodeNumber || 0) > epNum) || null

  return (
    <>
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      )}
      <EpisodeClient episode={episode} prevEpisode={prevEp} nextEpisode={nextEp} />
    </>
  )
}
