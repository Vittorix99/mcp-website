export function getApiErrorMessage(payload, fallback = "Errore generico dal server") {
  if (!payload || typeof payload !== "object") return fallback

  if (Array.isArray(payload.messages) && payload.messages.length) {
    return payload.messages.join(" ")
  }

  if (Array.isArray(payload.errors) && payload.errors.length) {
    return payload.errors.join(" ")
  }

  if (Array.isArray(payload.details) && payload.details.length) {
    const details = payload.details
      .map((detail) => {
        if (typeof detail === "string") return detail.trim()
        if (!detail || typeof detail !== "object") return ""

        const field = typeof detail.field === "string"
          ? detail.field
          : Array.isArray(detail.loc)
            ? detail.loc.join(".")
            : ""
        const message = detail.message || detail.msg
        if (typeof message !== "string" || !message.trim()) return ""
        return field ? `${field}: ${message}` : message
      })
      .filter(Boolean)

    if (details.length) return details.join(" ")
  }

  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message
  }

  if (typeof payload.error === "string" && payload.error.trim()) {
    return payload.error
  }

  return fallback
}
