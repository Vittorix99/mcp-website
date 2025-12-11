import { endpoints } from "../config/endpoints";

/**
 * Crea un ordine PayPal sul backend.
 * @param {Object} payload - Deve contenere il carrello (singolo oggetto o array).
 * @returns {Promise<Object>} - Dati dell’ordine o errore.
 */
export async function createOrder(payload) {
  try {
    const cart = payload?.cart || []
    const cartItems = Array.isArray(cart) ? cart : [cart]

    const response = await fetch(endpoints.createEventOrder, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ cart: cartItems }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Errore durante la creazione dell’ordine:", error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Cattura un ordine PayPal confermato dal client.
 * @param {string} order_id - ID dell’ordine da catturare.
 * @returns {Promise<Object>} - Dati del purchase registrato.
 */
export async function onApprove(order_id) {
  try {
    const response = await fetch(endpoints.captureEventOrder, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ order_id }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Errore durante la cattura dell’ordine:", error.message);
    return { success: false, error: error.message };
  }
}
