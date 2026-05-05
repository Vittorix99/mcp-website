import { endpoints } from "@/config/endpoints"

export async function getPublishedEpisodes() {
  try {
    const res = await fetch(endpoints.radio.getPublishedEpisodes)
    if (!res.ok) return { success: false, episodes: [] }
    const episodes = await res.json()
    return { success: true, episodes: Array.isArray(episodes) ? episodes : [] }
  } catch {
    return { success: false, episodes: [] }
  }
}

export async function getRadioSeasons() {
  try {
    const res = await fetch(endpoints.radio.getSeasons)
    if (!res.ok) return { success: false, seasons: [] }
    const seasons = await res.json()
    return { success: true, seasons: Array.isArray(seasons) ? seasons : [] }
  } catch {
    return { success: false, seasons: [] }
  }
}

export async function getLatestEpisode() {
  try {
    const res = await fetch(endpoints.radio.getLatestEpisode)
    if (!res.ok) return { success: false, episode: null }
    const episode = await res.json()
    return { success: true, episode: episode || null }
  } catch {
    return { success: false, episode: null }
  }
}
