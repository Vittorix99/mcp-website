import { endpoints } from '@/config/endpoints'
import { safeFetch } from '@/lib/fetch'

// ── Seasons ──────────────────────────────────────────────────────────────────

export async function getSeasons() {
  return safeFetch(endpoints.admin.radio.getSeasons, 'GET')
}

export async function getSeason(id) {
  return safeFetch(`${endpoints.admin.radio.getSeason}?id=${id}`, 'GET')
}

export async function createSeason(data) {
  return safeFetch(endpoints.admin.radio.createSeason, 'POST', data)
}

export async function updateSeason(id, data) {
  return safeFetch(endpoints.admin.radio.updateSeason, 'PUT', { id, ...data })
}

export async function deleteSeason(id) {
  return safeFetch(endpoints.admin.radio.deleteSeason, 'DELETE', { id })
}

// ── Episodes ─────────────────────────────────────────────────────────────────

export async function getEpisodes() {
  return safeFetch(endpoints.admin.radio.getEpisodes, 'GET')
}

export async function getEpisode(id) {
  return safeFetch(`${endpoints.admin.radio.getEpisode}?id=${id}`, 'GET')
}

export async function createEpisode(data) {
  return safeFetch(endpoints.admin.radio.createEpisode, 'POST', data)
}

export async function updateEpisode(id, data) {
  return safeFetch(endpoints.admin.radio.updateEpisode, 'PUT', { id, ...data })
}

export async function deleteEpisode(id) {
  return safeFetch(endpoints.admin.radio.deleteEpisode, 'DELETE', { id })
}

export async function publishEpisode(id) {
  return safeFetch(endpoints.admin.radio.publishEpisode, 'PATCH', { id })
}

export async function unpublishEpisode(id) {
  return safeFetch(endpoints.admin.radio.unpublishEpisode, 'PATCH', { id })
}
