import { safeFetch, safePublicFetch } from "@/lib/fetch"
import { endpoints } from "@/config/endpoints"

// ========== FUNZIONI SETTINGS ==========

/**
 * Ottieni il valore di una setting per chiave.
 * @param {string} key - Es. "payment_blocked"
 */
export async function getSetting(key) {
  const url = `${endpoints.admin.getSetting}?key=${key}`
  return safePublicFetch(url, 'GET')
}

/**
 * Ottieni tutte le settings dal backend.
 */
export async function getAllSettings() {
  return safeFetch(endpoints.admin.getSetting, 'GET')
}

/**
 * Imposta una setting per chiave.
 * @param {string} key
 * @param {any} value
 */
export async function setSetting(key, value) {
  return safeFetch(endpoints.admin.setSetting, 'POST', { key, value })
}