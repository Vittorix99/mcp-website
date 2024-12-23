import {endpoints} from '../config/endpoints';

export async function getNextEvent() {
    try {
      // Chiamata diretta alla Firebase Cloud Function
      const firebaseResponse = await fetch(
        endpoints.getNextEvent, // URL della tua Firebase Cloud Function per getNextEvent
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
  
      // Controllo se la risposta non è andata a buon fine
      if (!firebaseResponse.ok) {
        const errorText = await firebaseResponse.text();
        throw new Error(`Firebase Server Error: ${errorText}`);
      }
  
      // Ottengo i dati dell'evento dalla risposta
      const eventData = await firebaseResponse.json();
  
      // Restituisco i dati dell'evento per il chiamante
      return { success: true, event: eventData };
    } catch (error) {
      console.log('Error while fetching next event:', error.message);
  
      // Rilancio l'errore con un oggetto ben strutturato
      return { success: false, error: error.message };
    }
  }
  export async function getEventById(eventId) {
    try {
      // Chiamata diretta alla Firebase Cloud Function
      const endpointUrl = `${endpoints.getEventById}?id=${eventId}`;

      // Chiamata diretta alla Firebase Cloud Function
      const firebaseResponse = await fetch(endpointUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
  
      // Controllo se la risposta non è andata a buon fine
      if (!firebaseResponse.ok) {
        const errorText = await firebaseResponse.text();
        throw new Error(`Firebase Server Error: ${errorText}`);
      }
  
      // Ottengo i dati dell'evento dalla risposta
      const rawEventData = await firebaseResponse.json();
  
      // Verifica se l'evento esiste
      if (!rawEventData) {
        return {
          success: false,
          error: 'Event not found'
        };
      }
  
      // Formatto i dati dell'evento
      const formattedEvent = {
        id: rawEventData.id || eventId,
        title: rawEventData.title || '',
        date: rawEventData.date || '',
        startTime: rawEventData.startTime || '',
        endTime: rawEventData.endTime || '',
        location: rawEventData.location || '',
        lineup: Array.isArray(rawEventData.lineup) 
          ? rawEventData.lineup.filter(artist => artist && artist.trim() !== '')
          : [],
        note: rawEventData.note || '',
        active: Boolean(rawEventData.active),
        image: rawEventData.image || null,
        // Aggiungi campi opzionali se presenti
        ticketUrl: rawEventData.ticketUrl || null,
        capacity: rawEventData.capacity || null,
        price: rawEventData.price || null,
        minimumAge: rawEventData.minimumAge || null,
        dresscode: rawEventData.dresscode || null
      };
  
      // Restituisco i dati dell'evento formattati per il chiamante
      return {
        success: true,
        event: formattedEvent
      };
  
    } catch (error) {
      console.error('Error while fetching event:', error.message);
  
      // Rilancio l'errore con un oggetto ben strutturato
      return {
        success: false,
        error: error.message
      };
    }
  }

  export async function getAllEvents () {
    try {
      // Chiamata diretta alla Firebase Cloud Function
      const firebaseResponse = await fetch(
        endpoints.getAllEvents, // URL della tua Firebase Cloud Function per getAllEvents
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
  
      // Controllo se la risposta non è andata a buon fine
      if (!firebaseResponse.ok) {
        const errorText = await firebaseResponse.text();
        throw new Error(`Firebase Server Error: ${errorText}`);
      }
  
      // Ottengo i dati degli eventi dalla risposta
      const eventData = await firebaseResponse.json();
  
      // Restituisco i dati degli eventi per il chiamante
      return eventData;
    } catch (error) {
      console.error('Error while fetching all events:', error.message);
  
      // Rilancio l'errore con un oggetto ben strutturato
      return [];
    }
  }
