import { endpoints } from "@/config/endpoints"

const DEFAULT_REVALIDATE_SECONDS = 300

async function fetchJson(url, { revalidate = DEFAULT_REVALIDATE_SECONDS } = {}) {
  if (!url) return null

  try {
    const res = await fetch(url, { next: { revalidate } })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export async function getPublishedEpisodes(options = {}) {
  try {
    const episodes = await fetchJson(endpoints.radio.getPublishedEpisodes, options)
    return { success: true, episodes: Array.isArray(episodes) ? episodes : [] }
  } catch {
    return { success: false, episodes: [] }
  }
}

export async function getRadioSeasons(options = {}) {
  try {
    const seasons = await fetchJson(endpoints.radio.getSeasons, options)
    return { success: true, seasons: Array.isArray(seasons) ? seasons : [] }
  } catch {
    return { success: false, seasons: [] }
  }
}

export async function getLatestEpisode(options = {}) {
  try {
    const episode = await fetchJson(endpoints.radio.getLatestEpisode, options)
    return { success: true, episode: episode || null }
  } catch {
    return { success: false, episode: null }
  }
}

export async function getRadioEpisode(idOrSlug, options = {}) {
  if (!idOrSlug) return { success: false, episode: null }

  const key = encodeURIComponent(idOrSlug)
  const bySlug = await fetchJson(`${endpoints.radio.getEpisode}?slug=${key}`, options)
  if (bySlug) return { success: true, episode: bySlug }

  const byId = await fetchJson(`${endpoints.radio.getEpisode}?id=${key}`, options)
  return { success: Boolean(byId), episode: byId || null }
}
