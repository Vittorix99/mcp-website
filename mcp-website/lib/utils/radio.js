function _slugify(text) {
  return (text || "")
    .trim()
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "episode"
}

/**
 * Returns the episode's URL slug — uses the API-returned slug if present,
 * otherwise derives one from title + episodeNumber (matches Python slug_utils logic).
 * @param {object} episode
 * @returns {string}
 */
export function getEpisodeSlug(episode) {
  if (episode?.slug) return episode.slug
  const base = _slugify(episode?.title || "")
  return `${base}-ep-${episode?.episodeNumber ?? 0}`
}

/**
 * Converte millisecondi in formato leggibile "mm:ss" o "h:mm:ss"
 * @param {number} ms
 * @returns {string}
 */
export function formatDuration(ms) {
  if (!ms || isNaN(ms)) return '—'
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const pad = (n) => String(n).padStart(2, '0')
  if (hours > 0) return `${hours}:${pad(minutes)}:${pad(seconds)}`
  return `${minutes}:${pad(seconds)}`
}

/**
 * Converte una data ISO in formato leggibile "DD MMM YYYY"
 * @param {string|null} iso
 * @returns {string}
 */
export function formatDate(iso) {
  if (!iso) return '—'
  try {
    const date = new Date(iso)
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return '—'
  }
}
