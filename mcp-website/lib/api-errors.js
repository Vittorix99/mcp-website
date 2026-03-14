export function getApiErrorMessage(payload, fallback = "Errore generico dal server") {
  if (!payload || typeof payload !== "object") return fallback

  if (Array.isArray(payload.messages) && payload.messages.length) {
    return payload.messages.join(" ")
  }

  if (Array.isArray(payload.errors) && payload.errors.length) {
    return payload.errors.join(" ")
  }

  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message
  }

  if (typeof payload.error === "string" && payload.error.trim()) {
    return payload.error
  }

  return fallback
}
