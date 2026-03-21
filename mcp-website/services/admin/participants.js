import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

// CRUD e azioni extra
export async function getParticipantsByEvent(eventId) {
  return safeFetch(endpoints.admin.getParticipantsByEvent, 'POST', { eventId })
}

export async function getParticipantById(participantId) {
  return safeFetch(endpoints.admin.getParticipantById, 'POST', { participantId })
}

export async function createParticipant(participantData) {
  if (!participantData.event_id) {
    throw new Error("event_id mancante nella creazione partecipante");
  }

  return safeFetch(endpoints.admin.createParticipant, 'POST', participantData);
}
export async function updateParticipant(participantId, participantData) {
  
  return safeFetch(endpoints.admin.updateParticipant, 'PUT', {
    participantId,
    ...participantData,
  })
}

export async function deleteParticipant(participantId, data = {}) {
  return safeFetch(endpoints.admin.deleteParticipant, 'DELETE', {
    participantId,
    ...data,
  });
}
export async function sendLocationToParticipant({ eventId, participantId, address, link }) {
  return safeFetch(endpoints.admin.sendLocation, 'POST', {
    eventId,
    participantId,
    address,
    link,
  });
}
// Avvio job asincrono "send_location" (nuovo flusso)
export async function startSendLocationJobService({ eventId, address, link, message }) {
  return safeFetch(endpoints.admin.sendLocationToAll, 'POST', {
    eventId,
    address,
    link,
    message,
  });
}
export async function sendTicketToParticipant(participantId, eventId) {
  if (!participantId || !eventId) {
    throw new Error("participantId o eventId mancante per invio ticket");
  }

  return safeFetch(endpoints.admin.sendTicket, 'POST', {
    participantId,
    eventId
  });
}
