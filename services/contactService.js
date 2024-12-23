import {endpoints} from '../config/endpoints';
export async function sendContactRequest({ name, email, message, sendCopy = false }) {
    try {
      // Chiamata diretta alla Firebase Cloud Function
      const firebaseResponse = await fetch(
     endpoints.contactUs, // URL della tua Firebase Cloud Function
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name,
            email,
            message,
            send_copy: sendCopy,
          }),
        }
      );
  
      // Controllo se la risposta non è andata a buon fine
      if (!firebaseResponse.ok) {
        const errorText = await firebaseResponse.text();
        throw new Error(`Firebase Server Error: ${errorText}`);
      }
  
      // Ottengo il messaggio di successo dalla risposta (può essere JSON o testo)
      const responseData = await firebaseResponse.text();
  
      // Restituisco il messaggio per il chiamante
      return { success: true, message: responseData };
    } catch (error) {
      console.error('Error while sending contact request:', error.message);
  
      // Rilancio l'errore con un oggetto ben strutturato
      return { success: false, error: error.message };
    }
  }