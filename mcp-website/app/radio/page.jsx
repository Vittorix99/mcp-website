import RadioClient from "./RadioClient"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

const baseUrl = getBaseUrlFromEnv()

export const metadata = {
  title: "MCP Radio — Music Connecting People",
  description: "Listen to our radio episodes on SoundCloud. Electronic music mixes from MCP events and beyond.",
  alternates: baseUrl ? { canonical: `${baseUrl}/radio` } : undefined,
}

async function fetchEpisodes() {
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

async function fetchSeasons() {
  try {
    const SERVER_BASE =
      process.env.NEXT_PUBLIC_ENV === "production"
        ? "https://us-central1-mcp-website-2a1ad.cloudfunctions.net"
        : process.env.NEXT_PUBLIC_BASE_URL || "http://127.0.0.1:5001/mcp-website-2a1ad/us-central1"
    const res = await fetch(`${SERVER_BASE}/get_radio_seasons`, { next: { revalidate: 600 } })
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

export default async function RadioPage() {
  const [initialEpisodes, initialSeasons] = await Promise.all([fetchEpisodes(), fetchSeasons()])
  return <RadioClient initialEpisodes={initialEpisodes} initialSeasons={initialSeasons} />
}
