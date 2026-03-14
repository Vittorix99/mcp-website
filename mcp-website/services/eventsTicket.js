import { endpoints } from "@/config/endpoints";

/**
 * Controlla se i partecipanti sono già registrati per un evento
 * @param {string} eventId - ID dell'evento
 * @param {Array<Object>} participants - Array di partecipanti [{ name, surname, email, phone }]
 * @returns {Promise<{valid: boolean, errors?: string[]}>}
 */
export async function checkParticipants(eventId, participants) {
  try {
    const response = await fetch(endpoints.checkParticipants, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ eventId, participants }),
    });

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errors = Array.isArray(result?.messages)
        ? result.messages
        : Array.isArray(result?.errors)
          ? result.errors
          : [result?.message || result?.error || "Errore di validazione partecipanti."];
      return {
        valid: false,
        error: result?.error || "validation_error",
        errors,
      };
    }

    if (result?.valid === true) {
      return result;
    }

    if (Array.isArray(result?.messages) || Array.isArray(result?.errors) || result?.error) {
      const errors = Array.isArray(result?.messages)
        ? result.messages
        : Array.isArray(result?.errors)
          ? result.errors
          : [result?.message || result?.error || "Errore di validazione partecipanti."];
      return { valid: false, error: result?.error || "validation_error", errors };
    }

    return result;
  } catch (error) {
    console.error("Errore durante la verifica partecipanti:", error);
    return { valid: false, errors: ["Errore di rete"] };
  }
}
