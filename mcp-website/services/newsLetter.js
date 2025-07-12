import { endpoints } from "../config/endpoints"
export async function sendNewsLetterRequest({ email }) {
  try {
    // Recupera l'endpoint per la richiesta di iscrizione alla newsletter
    const endpointUrl = endpoints.newsletterSignup;

    // Effettua la richiesta
    const response = await fetch(endpointUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    // Controlla se la risposta non è andata a buon fine
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Newsletter Server Error: ${errorText}`);
    }

    // Ottieni il messaggio di risposta
    const responseData = await response.text();

    return { success: true, message: responseData };
  } catch (error) {
    console.error('Error while sending newsletter request:', error.message);

    // Ritorna un oggetto di errore strutturato
    return { success: false, error: error.message };
  }
}

export async function sendNewsLetterRequestParticipants(participants = []) {
  try {
    const endpointUrl = endpoints.newsletterSignup;

    // Validazione base
    if (!Array.isArray(participants) || participants.length === 0) {
      throw new Error("No participants provided for newsletter signup.");
    }

    // Opzionale: filtra solo quelli con email valida
    const validParticipants = participants.filter(
      (p) => p.email && typeof p.email === "string" && p.email.includes("@")
    );

    if (validParticipants.length === 0) {
      throw new Error("No valid emails provided for newsletter signup.");
    }

    const response = await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ participants: validParticipants }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Newsletter Server Error: ${errorText}`);
    }

    const responseData = await response.text();

    return { success: true, message: responseData };
  } catch (error) {
    console.error("Error while sending newsletter request:", error.message);
    return { success: false, error: error.message };
  }
}