import { endpoints } from '@/config/endpoints';
import { getToken } from '@/config/firebase';

/**
 * Client-side service functions for Admin Event Management
 */

async function safeFetch(url, method = 'GET', body = null) {
  try {
    const token = await getToken();
    if (!token) return { error: 'Token non disponibile' };

    const headers = {
      'Authorization': `Bearer ${token}`,
    };

    const options = {
      method,
      headers,
    };
    if (body !== null) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      return { error: data?.error || 'Errore generico dal server' };
    }

    return data || {};
  } catch (err) {
    console.error('Errore HTTP:', err);
    return { error: 'Errore di rete o del server.' };
  }
}

// 🆕 Crea un evento
export async function createEvent(eventData) {
  return safeFetch(endpoints.admin.createEvent, 'POST', eventData);
}

// ✏️ Aggiorna un evento
export async function updateEvent(eventId, eventData) {
  return safeFetch(endpoints.admin.updateEvent, 'PUT', {
    id: eventId,
    ...eventData,
  });
}

// ❌ Elimina un evento
export async function deleteEvent(eventId) {
  return safeFetch(endpoints.admin.deleteEvent, 'DELETE', { id: eventId });
}

// 📄 Ottieni tutti gli eventi
export async function getAllEventsAdmin() {
  return safeFetch(endpoints.admin.getAllEvents, 'GET');
}

// 🔍 Ottieni evento per ID
export async function getEventById(eventId) {
  return safeFetch(`${endpoints.admin.getEventById}?id=${eventId}`, 'GET');
}