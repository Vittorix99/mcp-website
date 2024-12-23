import endpoints from '../config/endpoints'; // Importa gli endpoint centralizzati

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