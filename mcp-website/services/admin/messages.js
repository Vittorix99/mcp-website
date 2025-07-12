import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

// GET: tutti i messaggi
export async function getAllMessages() {
  return await safeFetch(endpoints.admin.getAllMessages)
}

// GET: messaggio singolo per ID
export async function getMessageById(id) {
  if (!id) return { error: "ID mancante" }
  return await safeFetch(`${endpoints.admin.getMessageById}?id=${id}`)
}

// DELETE: messaggio per ID
export async function deleteMessage(messageId) {
  if (!messageId) return { error: "ID mancante" }
  return await safeFetch(endpoints.admin.deleteMessage, "DELETE", { message_id:messageId })
}

// POST: risposta a un messaggio
export async function replyToMessage({ email, body, subject = "Risposta al tuo messaggio", message_id }) {
  if (!email || !body || !message_id) return { error: "Email, corpo del messaggio o ID mancanti" }
  return await safeFetch(endpoints.admin.replyToMessage, "POST", { email, body, subject, message_id })
}