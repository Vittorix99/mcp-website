import { endpoints } from '@/config/endpoints';
import { safeFetch } from '@/lib/fetch';

/**
 * Client-side service functions for Admin Event Management
 */

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
