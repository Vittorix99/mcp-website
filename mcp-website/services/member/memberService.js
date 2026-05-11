import { endpoints } from '@/config/endpoints'
import { auth } from '@/config/firebase'

async function getMemberToken() {
  const user = auth.currentUser
  if (!user) return null
  return user.getIdToken()
}

async function memberFetch(url, method = 'GET', body = null) {
  const token = await getMemberToken()
  if (!token) return { error: 'Non autenticato', status: 401 }

  const headers = { Authorization: `Bearer ${token}` }
  const options = { method, headers, cache: 'no-store' }

  if (body !== null) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  try {
    const res = await fetch(url, options)
    const data = await res.json().catch(() => null)
    if (!res.ok) {
      return { error: data?.error || 'Errore del server', status: res.status }
    }
    return data || {}
  } catch (err) {
    console.error('memberFetch error:', err)
    return { error: 'Errore di rete', status: 0 }
  }
}

export async function getMemberProfile() {
  return memberFetch(endpoints.member.me)
}

export async function getMemberEvents() {
  return memberFetch(endpoints.member.events)
}

export async function getMemberPurchases() {
  return memberFetch(endpoints.member.purchases)
}

export async function getMemberTicket(eventId) {
  return memberFetch(`${endpoints.member.ticket}?event_id=${encodeURIComponent(eventId)}`)
}

export async function updateMemberPreferences(newsletterConsent) {
  return memberFetch(endpoints.member.preferences, 'PATCH', { newsletter_consent: newsletterConsent })
}

export async function getEventLocation(eventId) {
  return memberFetch(`${endpoints.member.getEventLocation}?event_id=${encodeURIComponent(eventId)}`)
}
