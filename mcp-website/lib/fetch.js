import { getToken as getAdminToken } from "@/config/firebase"
import { getApiErrorMessage } from "@/lib/api-errors"

/**
 * Safe fetch con gestione token, header, errori.
 */
export async function safeFetch(url, method = 'GET', body = null) {
  try {
    const token = await getAdminToken()
    if (!token) return { error: 'Token non disponibile' }

    const headers = {
      'Authorization': `Bearer ${token}`,
    }

    const options = {
      method,
      headers,
      cache: "no-store",
    }

    if (body !== null) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const message = getApiErrorMessage(data)
      const payload = data && typeof data === "object" ? data : {}
      return { ...payload, error: message, error_code: payload?.error, status: response.status }
    }

    return data || {}
  } catch (err) {
    console.error('Errore HTTP:', err)
    return { error: 'Errore di rete o del server.', status: 0 }
  }

}
export async function safePublicFetch(url, method = 'GET', body = null, fetchOptions = {}) {
  try {
    const headers = {}

    const options = {
      method,
      headers,
      ...fetchOptions,
    }

    if (body !== null) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const message = getApiErrorMessage(data)
      return { success: false, error: message, error_code: data?.error }
    }

    return { success: true, data: data || {} }
  } catch (err) {
    console.error('Errore HTTP:', err)
    return { success: false, error: 'Errore di rete o del server.' }
  }
}



export async function safeFetchId(url, method = 'GET', param = null) {
  try {
    // Aggiungi parametri come query string se presenti
    const fullUrl = param
      ? `${url}?${typeof param === "object"
          ? new URLSearchParams(param).toString()
          : `id=${encodeURIComponent(param)}`}`
      : url;

    const response = await fetch(fullUrl, {
      method,
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const message = getApiErrorMessage(data, "Errore sconosciuto")
      return { error: message, error_code: data?.error }
    }

    return data || {}
  } catch (error) {
    console.error("❌ safeFetchId error:", error);
    return { error: error.message || "Errore di rete" };
  }
}
