import { endpoints } from "@/config/endpoints"

export async function validateDiscountCode({ eventId, code, participantsCount, payerEmail, payerMembershipId = null }) {
  try {
    const response = await fetch(endpoints.validateDiscountCode, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        eventId,
        code,
        participantsCount,
        payerEmail,
        payerMembershipId,
      }),
    })

    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      return {
        valid: false,
        errorMessage: data?.message || data?.error || `HTTP ${response.status}`,
      }
    }
    return data
  } catch (error) {
    return {
      valid: false,
      errorMessage: error?.message || "Errore di rete o del server.",
    }
  }
}
