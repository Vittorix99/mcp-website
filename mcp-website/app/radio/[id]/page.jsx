import EpisodeClient from "./EpisodeClient"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()

async function fetchEpisode(id) {
  try {
    const SERVER_BASE =
      process.env.NEXT_PUBLIC_ENV === "production"
        ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
        : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1"
    const res = await fetch(`${SERVER_BASE}/get_radio_episode?id=${id}`, { next: { revalidate: 300 } })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

async function fetchAllEpisodes() {
  try {
    const SERVER_BASE =
      process.env.NEXT_PUBLIC_ENV === "production"
        ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
        : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1"
    const res = await fetch(`${SERVER_BASE}/get_published_radio_episodes`, { next: { revalidate: 300 } })
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

export async function generateMetadata({ params }) {
  const { id } = await params
  const episode = await fetchEpisode(id)
  if (!episode) return { title: "Episode — MCP Radio" }
  return {
    title: `${episode.title} — MCP Radio`,
    description: episode.description || "Listen to this MCP Radio episode on SoundCloud.",
    openGraph: episode.soundcloudArtworkUrl
      ? { images: [{ url: episode.soundcloudArtworkUrl }] }
      : undefined,
    alternates: baseUrl ? { canonical: `${baseUrl}/radio/${id}` } : undefined,
  }
}

export default async function EpisodePage({ params }) {
  const { id } = await params
  const [episode, allEpisodes] = await Promise.all([fetchEpisode(id), fetchAllEpisodes()])

  // Find prev/next in same season sorted by episodeNumber
  const sameSeasonEps = allEpisodes
    .filter(e => e.seasonId === episode?.seasonId && e.id !== id)
    .sort((a, b) => (a.episodeNumber || 0) - (b.episodeNumber || 0))

  const epNum = episode?.episodeNumber || 0
  const prevEp = sameSeasonEps.filter(e => (e.episodeNumber || 0) < epNum).at(-1) || null
  const nextEp = sameSeasonEps.find(e => (e.episodeNumber || 0) > epNum) || null

  return <EpisodeClient episode={episode} prevEpisode={prevEp} nextEpisode={nextEp} />
}
