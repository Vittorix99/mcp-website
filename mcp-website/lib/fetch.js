import { getToken as getAdminToken } from "@/config/firebase"

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
    }

    if (body !== null) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      return { error: data?.error || 'Errore generico dal server' }
    }

    return data || {}
  } catch (err) {
    console.error('Errore HTTP:', err)
    return { error: 'Errore di rete o del server.' }
  }

}
export async function safePublicFetch(url, method = 'GET', body = null) {
  try {
    const headers = {}

    const options = {
      method,
      headers,
    }

    if (body !== null) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      return { success: false, error: data?.error || 'Errore generico dal server' }
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

    const data = await response.json();

    if (!response.ok) {
      return { error: data.message || "Errore sconosciuto" };
    }

    return data;
  } catch (error) {
    console.error("❌ safeFetchId error:", error);
    return { error: error.message || "Errore di rete" };
  }
}